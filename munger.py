###
# munger.py - version 0.0.1
##

# a dead simple library for munging text streams; a pythonic answer to grep, sed
# and friends.
#
# convert a file's line endings:
# >>> Munger.open('/path/to/file').substitute(r"\r$", "").write()
#
# watch access logs for 404s:
# >>> m = munger.Munger.tail('access_log')
# >>> m.split().keep_if_field_matches(8, '404').field(6).display()
#
# find number of words containing "abc":
# >>> Munger.open('/usr/share/dict/words').keep_if_contains('abc').count()
#
# see modest test suite in munger_test.py for more basic examples of use.
#
# heavily inspired by Generator Tricks for Systems Programmers -- see
# http://dabeaz.com/generators.

import os
import re
import tempfile
import time

class Munger:
    def __init__(self, iter, file=None, path=None, parents=None):
        self.gen = (x for x in iter)
        self.file = file
        self.path = path
        self.temp_file = None
        self.temp_path = None
        self.parents = parents

    # spawn new Munger with this as the parent
    def spawn(self, gen):
        return Munger(gen, path=self.path, parents=[self])

    # if this has no parents, close any associated file; otherwise, close any
    # parents 
    def close(self):
        if self.parents is not None:
            for parent in self.parents:
                parent.close()
        if self.file is not None:
            self.file.close()
        if self.temp_file is not None:
            self.temp_file.close()
        
    # build Munger by looping over contents of a file
    @staticmethod
    def open(path):
        file = open(path)
        return Munger(file, file=file, path=path)
 
    # build Munger by "tail -f"ing a file
    @staticmethod
    def tail(path):
        file = open(path)
        return Munger(_tail(file), file=file, path=path)

    # make munger iterable
    def __iter__(self):
        return self

    # make munger iterable
    def next(self):
        return self.gen.next()

    # write to file
    def write(self, path=None):
        if path is None:
            self.write_to_temp()
            self.close()
            os.remove(self.path)
            os.rename(self.temp_path, self.path)
        else:
            file = open(path, "w")
            for x in self:
                file.write(x)
            file.close()
            self.close()
    
    # write to temporary file
    def write_to_temp(self):
        fh, path = tempfile.mkstemp()
        file = os.fdopen(fh, "w")

        for x in self:
            file.write(x)

        file.close()

        self.temp_file = file
        self.temp_path = path

    # display line by line
    def display(self):
        for x in self:
            if isinstance(x, str):
                print x,
            else:
                print x

    # compare with another Munger object
    def __eq__(self, other):
        return list(self) == list(other)

    ###
    # mappings
    ###
    def map(self, fn):
        # cannot use built-in map because we need a generator
        gen = (fn(x) for x in self)
        return self.spawn(gen)

    def substitute(self, pat, s):
        fn = lambda line: re.sub(pat, s, line)
        return self.map(fn)

    def split(self, delimiter=' '):
        fn = lambda line: tuple(line.split(delimiter))
        return self.map(fn)

    def join(self, delimiter=' '):
        fn = lambda tokens: delimiter.join(tokens)
        return self.map(fn)

    def map_on_field(self, ix, fn):
        fn1 = lambda tpl: tpl[:1] + tuple(fn(tpl[1])) + tpl[1+1:]
        return self.map(fn1)
 
    def field(self, ix):
        fn = lambda tpl: "%s\n" % tpl[ix]
        return self.map(fn)

    def keep_fields(self, *args):
        fn = lambda tpl: tuple([tpl[ix] for ix in args])
        return self.map(fn)

    def drop_fields(self, *args):
        fn = lambda tpl: tuple([tpl[ix] for ix in range(len(tpl)) if ix not in args])
        return self.map(fn)

    ###
    # filters
    ###
    def filter(self, fn):
        # cannot use built-in filter because we need a generator
        gen = (x for x in self if fn(x))
        return self.spawn(gen)
            
    def keep(self, fn):
        return self.filter(fn)

    def drop(self, fn):
        fn = lambda x: not fn(x)
        return self.filter(fn)
    
    def keep_on_field(self, ix, fn):
        fn1 = lambda lst: fn(lst[ix])
        return self.filter(fn1)

    def drop_on_field(self, ix, fn):
        fn1 = lambda lst: not fn(lst[ix])
        return self.filter(fn1)

    def keep_if_matches(self, pat):
        fn = lambda line: re.match(pat, line)
        return self.filter(fn)

    def drop_if_matches(self, pat):
        fn = lambda line: not re.match(pat, line)
        return self.filter(fn)

    def keep_if_contains(self, pat):
        fn = lambda line: re.search(pat, line)
        return self.filter(fn)

    def drop_if_contains(self, pat):
        fn = lambda line: not re.search(pat, line)
        return self.filter(fn)

    def keep_if_field_matches(self, ix, pat):
        fn = lambda line: re.match(pat, line)
        return self.keep_on_field(ix, fn)

    def drop_if_field_matches(self, ix, pat):
        fn = lambda line: not re.match(pat, line)
        return self.drop_on_field(ix, fn)

    def keep_if_field_contains(self, ix, pat):
        fn = lambda line: re.search(pat, line)
        return self.keep_on_field(ix, fn)

    def drop_if_field_contains(self, ix, pat):
        fn = lambda line: not re.search(pat, line)
        return self.drop_on_field(ix, fn)

    ###
    ###
    # reductions
    ###
    def reduce(self, fn, base):
        out = reduce(fn, self, base)
        self.close()
        return out

    def count(self):
        fn = lambda acc, x: 1 + acc
        return self.reduce(fn, 0)

    ###
    # sorts
    ###
    def sort(self, **kwargs):
        gen = iter(sorted(self, **kwargs))
        m1 = self.spawn(gen)
        m1.write_to_temp()
        m2 = Munger.open(m1.temp_path)
        self.close()
        m1.close()
        return m2

    def sort_asc(self, **kwargs):
        if 'reverse' in kwargs:
            raise Exception
        return self.sort(**kwargs)

    def sort_desc(self, **kwargs):
        if 'reverse' in kwargs:
            raise Exception
        return self.sort(reverse=True, **kwargs)

    ###
    # merge
    ###
    @staticmethod
    def merge(*ms, **kwargs):
        return Munger(_merge(*ms, **kwargs), parents=ms)

###
# utilities
###
def _tail(file):
    file.seek(0, os.SEEK_END)
    try:
        while True:
            line = file.readline()
            if not line:
                time.sleep(0.01)
                continue
            yield line
    except KeyboardInterrupt:
        pass

# behaviour undefined if munger arguments are not already sorted
def _merge(*ms, **kwargs):
    if 'cmp' in kwargs:
        cmp = kwargs['cmp']
    else:
        cmp = globals()['__builtins__']['cmp']

    ms = list(ms)
    xs = [m.next() for m in ms]
    while xs:
        next_element = sorted(xs, cmp)[0]
        ix = xs.index(next_element)
        yield xs[ix]
        try:
            xs[ix] = ms[ix].next() 
        except StopIteration:
            ms.remove(ms[ix])
            xs.remove(xs[ix])
