import numpy as np
import operator as op

from nose.tools import assert_equal, assert_true, assert_false, assert_raises
from numpy.testing import assert_equal, assert_array_equal, \
    assert_array_less

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

    obs = sis.reduce(a, {'x': ('==', 1)})
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
    obs = sis.reduce(a, {'x': ('>', 1), 'y': ('<', 15)})
    yield assert_equal, obs, a[2:-5]
    
def test_id_tree():
    data = [{'paramid': 'a', 'instid': 'b', 'solnid': 'c', 'solver': 'x'},
            {'paramid': 'a', 'instid': 'b', 'solnid': 'd', 'solver': 'y'}]
    tree = sis.id_tree(data)
    assert_equal(len(tree), 1)
    for pid, pst in sis.subtrees(tree):
        assert_equal(pid, 'a')
        assert_equal(len(pst), 1)
        for iid, ist in sis.subtrees(pst):
            assert_equal(iid, 'b')
            assert_equal(len(ist), 2)
            sids = set([x for x, _ in sis.subtrees(ist)])
            assert_equal(sids, set(['c', 'd']))
            solvers = set([x for _, x in sis.subtrees(ist)])
            assert_equal(solvers, set(['x', 'y']))

def test_id_tree_prune():
    data = [{'paramid': 'a', 'instid': 'b', 'solnid': 'c', 'solver': 'x'},
            {'paramid': 'a', 'instid': 'b', 'solnid': 'd', 'solver': 'y'},
            {'paramid': 'a', 'instid': 'c', 'solnid': 'd', 'solver': 'y'},
            {'paramid': 'b', 'instid': 'z', 'solnid': 'x', 'solver': 'y'},
            {'paramid': 'b', 'instid': 'c', 'solnid': 'd', 'solver': 'y'},
            {'paramid': 'b', 'instid': 'c', 'solnid': 'x', 'solver': 'y'},]
            
    obs = sis.id_tree(data, nsoln_prune=0)
    exp = sis.Tree()
    assert_equal(obs, exp)

    obs = sis.id_tree(data, nsoln_prune=1)
    exp = sis.Tree()
    exp['a']['c']['d'] = 'y'
    exp['b']['z']['x'] = 'y'
    assert_equal(obs, exp)

    obs = sis.id_tree(data, nsoln_prune=2)
    exp = sis.Tree()
    exp['a']['b']['c'] = 'x'
    exp['a']['b']['d'] = 'y'
    exp['b']['c']['d'] = 'y'
    exp['b']['c']['x'] = 'y'
    assert_equal(obs, exp)

def test_id_tree_prune2():
    data = [{'paramid': 'a', 'instid': 'b', 'solnid': 'd', 'solver': 'x'},
            {'paramid': 'a', 'instid': 'b', 'solnid': 'e', 'solver': 'y'},
            {'paramid': 'a', 'instid': 'b', 'solnid': 'f', 'solver': 'z'},
            {'paramid': 'b', 'instid': 'a', 'solnid': 'g', 'solver': 'x'},
            {'paramid': 'b', 'instid': 'a', 'solnid': 'h', 'solver': 'y'},
            {'paramid': 'b', 'instid': 'a', 'solnid': 'i', 'solver': 'z'},]

    exp = sis.Tree()
    assert_equal(exp, sis.id_tree(data, nsoln_prune=0))
    assert_equal(exp, sis.id_tree(data, nsoln_prune=1))
    assert_equal(exp, sis.id_tree(data, nsoln_prune=2))
    assert_equal(exp, sis.id_tree(data, nsoln_prune=4))

    exp['a']['b']['d'] = 'x'
    exp['a']['b']['e'] = 'y'
    exp['a']['b']['f'] = 'z'
    exp['b']['a']['g'] = 'x'
    exp['b']['a']['h'] = 'y'
    exp['b']['a']['i'] = 'z'
    assert_equal(exp, sis.id_tree(data, nsoln_prune=3))
    
def test_id_tree_from_file():
    from cyclopts import exchange_family
    from cyclopts.structured_species import request 

    fname = './files/test_comb_2_solvers.h5'
    fam = exchange_family.ResourceExchange()
    sp = request.StructuredRequest()
    data = sis.cyclopts_data(fname, fam, sp)

    tree = sis.id_tree(data, nsoln_prune=2)
    assert_equal(len(tree), 4)
    for pid, pst in sis.subtrees(tree):
        assert_equal(len(pst), 1)
        for iid, ist in sis.subtrees(pst):
            assert_equal(len(ist), 2)
            solvers = set([solver for _, solver in sis.subtrees(ist)])
            assert_equal(solvers, set(['cbc', 'greedy']))

def test_nnodes():
    data = [{'paramid': 'a', 'instid': 'b', 'solnid': 'd', 'solver': 'x'},
            {'paramid': 'a', 'instid': 'b', 'solnid': 'e', 'solver': 'y'},
            {'paramid': 'a', 'instid': 'c', 'solnid': 'f', 'solver': 'z'},
            {'paramid': 'a', 'instid': 'c', 'solnid': 'g', 'solver': 'a'},
            {'paramid': 'b', 'instid': 'a', 'solnid': 'h', 'solver': 'x'},
            {'paramid': 'b', 'instid': 'a', 'solnid': 'i', 'solver': 'y'},
            {'paramid': 'b', 'instid': 'a', 'solnid': 'j', 'solver': 'z'},
            {'paramid': 'b', 'instid': 'd', 'solnid': 'k', 'solver': 'a'},]
    tree = sis.id_tree(data)
    assert_equal(sis.nnodes(tree, lev=0), 2)
    assert_equal(sis.nnodes(tree, lev=1), 4)
    assert_equal(sis.nnodes(tree, lev=2), 8)
            
def test_ninsts():
    data = [{'paramid': 'a', 'instid': 'b', 'solnid': 'c', 'solver': 'x'},
            {'paramid': 'a', 'instid': 'b', 'solnid': 'd', 'solver': 'y'}]
    tree = sis.id_tree(data)
    assert_equal(sis.ninsts(tree), 1)
    
    data.append({'paramid': 'a', 'instid': 'bx', 'solnid': 'c', 'solver': 'x'})
    data.append({'paramid': 'a', 'instid': 'by', 'solnid': 'd', 'solver': 'y'})
    tree = sis.id_tree(data)
    assert_equal(sis.ninsts(tree), 3)

def test_leaf_vals():
    data = [{'paramid': 'a', 'instid': 'b', 'solnid': 'c', 'solver': 'x'},
            {'paramid': 'a', 'instid': 'b', 'solnid': 'd', 'solver': 'y'}]
    tree = sis.id_tree(data)
    assert_equal(sis.leaf_vals(tree), set(['x', 'y']))

def test_flow_rms():
    from cyclopts import exchange_family
    from cyclopts.structured_species import request

    fname = './files/test_comb_2_solvers.h5'
    fam = exchange_family.ResourceExchange()
    sp = request.StructuredRequest()
    data = sis.cyclopts_data(fname, fam, sp)
    tree = sis.id_tree(data)
    ret = sis.flow_rms(fname, tree, 'StructuredRequest')
    assert_array_equal(ret['cflows']['cbc'], ret['cflows']['greedy'])
    assert_array_equal(ret['flows']['cbc'], ret['flows']['greedy'])

def test_flow_rms_diff():
    from cyclopts import exchange_family
    from cyclopts.structured_species import request
    from cyclopts.functionals import rms

    fname = './files/test_comb_2_solvers.h5'
    fam = exchange_family.ResourceExchange()
    sp = request.StructuredRequest()
    data = sis.cyclopts_data(fname, fam, sp)
    tree = sis.id_tree(data)
    
    ret = sis.flow_rms_diff(fname, tree, 'StructuredRequest', base_solver='cbc')
    # This may fail if the db is regenerated with a new 'cyclopts exec', but I
    # think everything is small enough that this will always be true. Ordering
    # may also change, but I don't expect that to be the case.
    exp = [
        rms(np.array([17500, 17500, 0, 0])), 
        rms(np.array([17500, 17500, 0])),
        0,
        0,
        ]
    obs = ret['flows']['greedy']
    assert_array_equal(obs, exp)

    exp = [
        rms(0.5 * np.array([17500, 17500, 0, 0])), 
        rms(0.5 * np.array([17500, 17500, 0])),
        0,
        0,
        ]
    obs = ret['cflows']['greedy']
    assert_array_equal(obs, exp)
    
