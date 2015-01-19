import numpy as np
import operator as op

from nose.tools import assert_equal, assert_true, assert_false, assert_raises
from numpy.testing import assert_equal

import cyclopts.analysis as sis

def test_value_split():
    a = np.array(zip(range(10), range(10, 20)), dtype=[('x', int), ('y', int)])
    x, y = sis.value_split(a, 'x', 7)
    yield assert_equal, x, a[:8]
    yield assert_equal, y, a[8:]
    x, y = sis.value_split(a, 'y', 11)
    yield assert_equal, x, a[:2]
    yield assert_equal, y, a[2:]

def test_cleanse():
    a = np.array(zip(range(10), range(10, 20)), dtype=[('x', int), ('y', int)])
    b = np.array(zip(range(10), range(10, 20)), dtype=[('x', int), ('y', int)])
    x, y = sis.cleanse(a, b, 'x')
    yield assert_equal, x, a
    yield assert_equal, y, b
    x, y = sis.cleanse(a, b, 'y')
    yield assert_equal, x, a
    yield assert_equal, y, b

    c = np.array(zip(range(11), range(10, 21)), dtype=[('x', int), ('y', int)])
    x, y = sis.cleanse(a, c, 'x')
    yield assert_equal, x, a
    yield assert_equal, y, c[:-1]
    x, y = sis.cleanse(a, c, 'y')
    yield assert_equal, x, a
    yield assert_equal, y, c[:-1]

    b[0]['y'] = -1
    x, y = sis.cleanse(a, b, 'x')
    yield assert_equal, x, a
    yield assert_equal, y, b
    x, y = sis.cleanse(a, b, 'y')
    yield assert_equal, x, a[1:]
    yield assert_equal, y, b[1:]

def test_split_group_by():
    a = np.array(zip([0, 2, 1, 3], [1, 5, 3, 6]), dtype=[('x', int), ('y', int)])
    b = np.array(zip([3, 1, 2, 0], [4, 2, 3, 1]), dtype=[('x', int), ('y', int)])
    
    xs, ys = sis.split_group_by(a, b, 'y', 2, 'x')
    yield assert_equal, xs[0], a[0:1]
    yield assert_equal, ys[0], b[0:1]
    yield assert_equal, xs[1], a[1:2]
    yield assert_equal, ys[1], b[1:2]
    yield assert_equal, xs[2], a[2:]
    yield assert_equal, ys[2], b[2:]

def test_reduce():
    a = np.array(zip(range(10), range(10, 20)), dtype=[('x', int), ('y', int)])

    obs = sis.reduce(a, {'x': 1}, op.eq)
    yield assert_equal, obs, a[1:2]
    obs = sis.reduce_eq(a, {'x': 1})
    yield assert_equal, obs, a[1:2]
    obs = sis.reduce_gt(a, {'x': 1})
    yield assert_equal, obs, a[2:]
    obs = sis.reduce_lt(a, {'x': 1})
    yield assert_equal, obs, a[:1]
    obs = sis.reduce_in(a, {'x': range(1, 9)})
    yield assert_equal, obs, a[1:-1]
    obs = sis.reduce_not_in(a, {'x': range(1, 9)})
    yield assert_equal, obs, np.concatenate((a[:1], a[-1:]))
    
def test_trees():
    from cyclopts import exchange_family
    from cyclopts.structured_species import request 
    fname = './files/test_comb.h5'
    fam = exchange_family.ResourceExchange()
    sp = request.StructuredRequest()
    data = sis.cyclopts_data(fname, fam, sp)
    print(data)

    trees = sis.id_trees(data, nsoln=1)
    
