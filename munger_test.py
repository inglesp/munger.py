from unittest import TestCase, main
from munger import *

class MapTest(TestCase):
    def setUp(self):
        self.munger1 = Munger(['A|a', 'B|b', 'C|c'])
        self.munger2 = Munger([('A', 'a'), ('B', 'b'), ('C', 'c')])

    def test_substitute(self):
        out = self.munger1.substitute('\|', ':')
        self.assertEqual(out, ['A:a', 'B:b', 'C:c'])
        
    def test_split(self):
        out = self.munger1.split('|')
        self.assertEqual(out, self.munger2)

    def test_join(self):
        out = self.munger2.join('|')
        self.assertEqual(out, self.munger1)

    def test_map_on_field(self):
        out = self.munger2.map_on_field(1, lambda c: chr(ord(c) + 1))
        self.assertEqual(out, [('A', 'b'), ('B', 'c'), ('C', 'd')])

    def test_keep_fields(self):
        out = self.munger2.keep_fields(0)
        self.assertEqual(out, [('A',), ('B',), ('C',)])

    def test_drop_fields(self):
        out = self.munger2.drop_fields(0)
        self.assertEqual(out, [('a',), ('b',), ('c',)])


class FilterTest(TestCase):
    def setUp(self):
        self.munger1 = Munger(['abc', 'abd', 'acd', 'bcd'])
        self.munger2 = Munger([('abc', 'def'), ('uvw', 'xyz')])
        self.out1 = ['abc', 'abd']
        self.out2 = ['acd', 'bcd']
        self.out3 = [('abc', 'def')]

    def test_keep_if_matches(self):
        out = self.munger1.keep_if_matches('ab.*')
        self.assertEqual(out, self.out1)

    def test_drop_if_matches(self):
        out = self.munger1.drop_if_matches('ab.*')
        self.assertEqual(out, self.out2)

    def test_keep_if_contains(self):
        out = self.munger1.keep_if_contains('ab')
        self.assertEqual(out, self.out1)

    def test_drop_if_contains(self):
        out = self.munger1.drop_if_contains('ab')
        self.assertEqual(out, self.out2)

    def test_keep_on_field(self):
        out = self.munger2.keep_on_field(0, lambda x: x == 'abc')
        self.assertEqual(out, self.out3)

    def test_drop_on_field(self):
        out = self.munger2.drop_on_field(0, lambda x: x != 'abc')
        self.assertEqual(out, self.out3)


class ReduceTest(TestCase):
    def setUp(self):
        lst = ['abc', 'abd', 'acd', 'bcd']
        self.m = Munger(lst)
    
    def test_count(self):
        self.assertEqual(self.m.count(), 4)


class SortTest(TestCase):
    def setUp(self):
        lst = ['abd\n', 'abc\n', 'bcd\n', 'acd\n']
        self.m = Munger(lst)
        self.sorted_asc = ['abc\n', 'abd\n', 'acd\n', 'bcd\n']
        self.sorted_desc = ['bcd\n', 'acd\n', 'abd\n', 'abc\n']

    def test_sort_asc(self):
        out = self.m.sort_asc()
        self.assertEqual(out, self.sorted_asc)

    def test_sort_desc(self):
        out = self.m.sort_desc()
        self.assertEqual(out, self.sorted_desc)


class MergeTest(TestCase):
    def setUp(self):
        lst1 = [1, 3, 5, 7]
        lst2 = [2, 4, 6, 8]
        lst3 = [0, 3, 6, 9]
        self.m1 = Munger(lst1)
        self.m2 = Munger(lst2)
        self.m3 = Munger(lst3)

    def test_merge_2(self):
        out = Munger.merge(self.m1, self.m2)
        self.assertEqual(out, [1, 2, 3, 4, 5, 6, 7, 8])

    def test_merge_3(self):
        out = Munger.merge(self.m1, self.m2, self.m3)
        self.assertEqual(out, [0, 1, 2, 3, 3, 4, 5, 6, 6, 7, 8, 9])


if __name__ == "__main__":
    main()

