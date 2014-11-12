import numpy as np

from nose.tools import assert_equal, assert_true, assert_false, assert_raises
from numpy.testing import assert_equal

import cyclopts.analysis as sis

def test_value_split():
    a = np.array(zip(range(10), range(10, 20)), dtype=[('x', int), ('y', int)])
    x, y = sis.value_split(a, 'x', 7)
    assert_equal(x, a[:8])
    assert_equal(y, a[8:])
    x, y = sis.value_split(a, 'y', 11)
    assert_equal(x, a[:2])
    assert_equal(y, a[2:])

def test_cleanse():
    a = np.array(zip(range(10), range(10, 20)), dtype=[('x', int), ('y', int)])
    b = np.array(zip(range(10), range(10, 20)), dtype=[('x', int), ('y', int)])
    x, y = sis.cleanse(a, b, 'x')
    assert_equal(x, a)
    assert_equal(y, b)
    x, y = sis.cleanse(a, b, 'y')
    assert_equal(x, a)
    assert_equal(y, b)

    c = np.array(zip(range(11), range(10, 21)), dtype=[('x', int), ('y', int)])
    x, y = sis.cleanse(a, c, 'x')
    assert_equal(x, a)
    assert_equal(y, c[:-1])
    x, y = sis.cleanse(a, c, 'y')
    assert_equal(x, a)
    assert_equal(y, c[:-1])

    b[0]['y'] = -1
    x, y = sis.cleanse(a, b, 'x')
    assert_equal(x, a)
    assert_equal(y, b)
    x, y = sis.cleanse(a, b, 'y')
    assert_equal(x, a[1:])
    assert_equal(y, b[1:])

def test_split_group_by():
    a = np.array(zip([0, 2, 1, 3], [1, 5, 3, 6]), dtype=[('x', int), ('y', int)])
    b = np.array(zip([3, 1, 2, 0], [4, 2, 3, 1]), dtype=[('x', int), ('y', int)])
    
    xs, ys = sis.split_group_by(a, b, 'y', 2, 'x')
    assert_equal(xs[0], a[0:1])
    assert_equal(ys[0], b[0:1])
    assert_equal(xs[1], a[1:2])
    assert_equal(ys[1], b[1:2])
    assert_equal(xs[2], a[2:])
    assert_equal(ys[2], b[2:])
