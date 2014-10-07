from cyclopts.random_request_species import RandomRequest, RandomRequestPoint, \
    RandomRequestBuilder, PathMap

import numpy as np
import os

import nose
from nose.tools import assert_equal, assert_almost_equal, assert_true, \
    assert_false, assert_raises, assert_less, assert_greater, \
    assert_less_equal, assert_greater_equal

from utils import assert_cyc_equal
from cyclopts.exchange_instance import ExGroup, ExNode, ExArc
from cyclopts.exchange_family import ResourceExchange
from cyclopts.params import Param, BoolParam, CoeffParam, SupConstrParam
from cyclopts.tools import parse_rc

def test_basics():
    sp = RandomRequest()
    assert_equal(sp.name, 'RandomRequest')
    assert_true(isinstance(sp.family, ResourceExchange))
    
    sp.read_space({'n_commods': {'avg': range(1, 3)},
                   'n_supply': {'avg': range(1, 3)},
                   'n_request': {'avg': range(1, 3)}})
    i = 0
    assert_equal(len(range(1, 3)) ** 3, sp.n_points)
    for p in sp.points():
        i += 1
    assert_equal(i, 5)

    base = '/Species/RandomRequest'
    col, tbl = 'n_request_avg', 'RandomRequestParameters'
    assert_equal(PathMap(col).path, base + '/' + tbl)
    
def invalid_rr_builder():
    s = RandomRequestPoint()
    assert_equal(2, s.n_commods.sample())
    assert_equal(1, s.n_supply.sample())
    b = RandomRequestBuilder(s)
    assert_false(b.valid())

def test_def_rxtr_req_sample():
    s = RandomRequestPoint()
    assert_equal(1, s.n_commods.sample())
    assert_equal(1, s.n_request.sample())
    assert_equal(1, s.assem_per_req.sample())
    assert_false(s.assem_multi_commod.sample())
    assert_equal(0, s.req_multi_commods.sample())
    assert_false(s.exclusive.sample())
    assert_equal(0, s.n_req_constr.sample())
    assert_equal(1, s.n_supply.sample())
    assert_equal(0, s.sup_multi.sample())
    assert_equal(0, s.sup_multi_commods.sample())
    assert_equal(1, s.n_sup_constr.sample())
    assert_equal(1, s.sup_constr_val.sample())
    assert_true(s.connection.sample())
    s1 = RandomRequestPoint()
    assert_equal(s1, s)
    constr_avg = 0
    pref_avg = 0
    n = 5000
    for i in range(n):
        constr = s.constr_coeff.sample()
        constr_avg += constr
        assert_greater(constr,  0)
        assert_less_equal(constr,  2)
        pref = s.pref_coeff.sample()
        pref_avg += pref
        assert_greater(pref,  0)
        assert_less_equal(pref,  1)
    assert_almost_equal(1.0, constr_avg / n, places=1)
    assert_almost_equal(0.5, pref_avg / n, places=1)

def test_def_rxtr_req_build():
    s = RandomRequestPoint()
    b = RandomRequestBuilder(s)
    groups, nodes, arcs = b.build()
    req = True
    bid = False
    assert_equal(len(groups), 2)
    assert_equal(len(nodes), 2)
    assert_equal(len(arcs), 1)
    assert_equal(groups[0].id, nodes[0].gid)
    assert_equal(groups[1].id, nodes[1].gid)
    exp = ExGroup(0, req, np.array([1], dtype='float'), [req], 1)
    assert_cyc_equal(exp, groups[0])
    exp = ExGroup(1, bid, np.array([1], dtype='float'), [bid])
    assert_cyc_equal(exp, groups[1])
    exp = ExNode(0, 0, req, 1)
    assert_cyc_equal(exp, nodes[0])
    exp = ExNode(1, 1, bid, 1)
    assert_cyc_equal(exp, nodes[1])
    # arcs are separate because values are stochastic
    exp = ExArc(0, 0, np.array([1], dtype='float'), 
                1, np.array([1], dtype='float'), 1)
    assert_equal(exp.id, arcs[0].id)
    assert_equal(exp.uid, arcs[0].uid)
    assert_equal(exp.vid, arcs[0].vid)
    assert_equal(len(arcs[0].ucaps), 1)
    assert_greater(arcs[0].ucaps,  0)
    assert_less_equal(arcs[0].ucaps,  2)
    assert_equal(len(arcs[0].vcaps), 1)
    assert_greater(arcs[0].vcaps,  0)
    assert_less_equal(arcs[0].vcaps,  2)
    assert_greater(arcs[0].pref,  0)
    assert_less_equal(arcs[0].pref,  1)

def test_rxtr_req_build_changes():
    s = RandomRequestPoint()
    
    # more than one commod without more than one supplier
    s.n_commods = Param(2)
    b = RandomRequestBuilder(s)
    assert_raises(ValueError, b.build)
    s.n_commods = Param(1)

    # exclusive request node
    s.exclusive = BoolParam(1)
    b = RandomRequestBuilder(s)
    groups, nodes, arcs = b.build()
    excls = [n.id for n in nodes if n.excl]
    assert_equal(len(excls), 1)
    assert_equal(excls[0], 0)
    s.exclusive = BoolParam(-1)

    # 2 suppliers 0 connection prob
    s.connection = BoolParam(0)
    s.n_supply = Param(2)
    b = RandomRequestBuilder(s)
    groups, nodes, arcs = b.build()
    assert_equal(len(arcs), 1)
    s.connection = BoolParam(1)
    s.n_supply = Param(1)

    # 2 suppliers, 2 commods, 2 req nodes, 4 arcs
    s.n_commods = Param(2)
    s.n_supply = Param(2)
    s.assem_multi_commod = BoolParam(1)
    s.req_multi_commods = Param(1)
    s.sup_multi = BoolParam(1)
    s.sup_multi_commods = Param(1)
    b = RandomRequestBuilder(s)
    groups, nodes, arcs = b.build()
    assert_equal(len(arcs), 4)
    commods = b._assem_commods(set([0, 1]))
    assert_true(0 in commods and 1 in commods)
    assign = b._assign_supply_commods([0, 1], [0, 1])
    assert_equal(assign[1][0], assign[0][1])
    assert_equal(assign[1][1], assign[0][0])
    s.n_commods = Param(1)
    s.n_supply = Param(1)
    s.assem_multi_commod = BoolParam(-1)
    s.req_multi_commods = Param(0)
    s.sup_multi = BoolParam(-1)

    # n constraints
    s.n_req_constr = Param(2)
    s.n_sup_constr = Param(3)
    b = RandomRequestBuilder(s)
    groups, nodes, arcs = b.build()
    assert_equal(len(groups[0].caps), 2 + 1) # +1 for default constraint
    assert_equal(len(groups[1].caps), 3)
    assert_equal(len(arcs[0].ucaps), 2 + 1)
    assert_equal(len(arcs[0].vcaps), 3)
    s.n_sup_constr = Param(1)
    s.n_req_constr = Param(1)
    
