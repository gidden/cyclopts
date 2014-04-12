from cyclopts.params import Incrementer, Param, BoolParam, ReactorRequestSampler, ReactorRequestBuilder
from cyclopts.execute import GraphParams
from nose.tools import assert_equal, assert_almost_equal, assert_true, \
    assert_false, assert_raises

def test_incr():
    i = Incrementer()
    assert_equal(i.next(), 0)
    i = Incrementer(5)
    assert_equal(i.next(), 5)
    assert_equal(i.next(), 6)

def test_def_rxtr_req_sample():
    s = ReactorRequestSampler()
    assert_equal(1, s.n_commods.sample())
    assert_equal(1, s.n_request.sample())
    assert_equal(1, s.assem_per_req.sample())
    assert_false(s.assem_multi_commod.sample())
    assert_equal(0, s.req_multi_commods.sample())
    assert_false(s.exclusive.sample())
    assert_equal(0, s.n_req_constr.sample())
    assert_equal(1, s.n_supply.sample())
    assert_equal(0, s.sup_multi.sample())
    assert_equal(1, s.sup_multi_commods.sample())
    assert_equal(1, s.n_sup_constr.sample())
    assert_equal(1, s.sup_constr_val.sample())
    assert_true(s.connection.sample())
    constr_avg = 0
    pref_avg = 0
    n = 1000
    for i in range(n):
        constr = s.constr_coeff.sample()
        constr_avg += constr
        assert_true(constr > 0)
        assert_true(constr <= 1)
        pref = s.pref_coeff.sample()
        pref_avg += pref
        assert_true(pref > 0)
        assert_true(pref <= 1)
    assert_almost_equal(0.5, constr_avg / n, places=1)
    assert_almost_equal(0.5, pref_avg / n, places=1)

def test_def_rxtr_req_build():
    s = ReactorRequestSampler()
    p = GraphParams()
    b = ReactorRequestBuilder(s, p)
    b.build()
    assert_equal(len(p.u_nodes_per_req), 1)
    assert_equal(len(p.v_nodes_per_sup), 1)
    assert_equal(p.u_nodes_per_req[0][0], 0)
    assert_equal(p.v_nodes_per_sup[1][0], 1)
    assert_equal(len(p.req_qty), 1)
    assert_equal(p.req_qty[0], 1)
    assert_equal(len(p.constr_vals), 2)
    assert_equal(len(p.constr_vals[0]), 0)
    assert_equal(len(p.constr_vals[1]), 1)
    assert_equal(p.constr_vals[1], 1)
    assert_equal(len(p.def_constr_coeff), 1)
    assert_equal(p.def_constr_coeff[0], 1)
    assert_equal(len(p.node_qty), 2)
    assert_equal(p.node_qty[0], 1)
    assert_true(p.node_qty[1] > 1e100)
    assert_equal(len(p.node_excl), 2)
    assert_false(p.node_excl[0])
    assert_false(p.node_excl[1])
    assert_equal(len(p.excl_req_nodes), 1)
    assert_equal(len(p.excl_req_nodes[0]), 0)
    assert_equal(len(p.excl_sup_nodes), 1)
    assert_equal(len(p.excl_sup_nodes[1]), 0)
    assert_equal(len(p.node_ucaps), 2)
    assert_equal(len(p.node_ucaps[0]), 1)
    assert_equal(len(p.node_ucaps[1]), 1)
    assert_equal(len(p.node_ucaps[0][0]), 0)
    assert_equal(len(p.node_ucaps[1][0]), 1)
    assert_equal(len(p.arc_to_unode), 1)
    assert_equal(p.arc_to_unode[0], 0)
    assert_equal(len(p.arc_to_vnode), 1)
    assert_equal(p.arc_to_vnode[0], 1)
    assert_equal(len(p.arc_pref), 1)
    assert_true(p.arc_pref[0] > 0 and p.arc_pref[0] <= 1)

def test_rxtr_req_build_changes():
    s = ReactorRequestSampler()
    
    # more than one commod without more than one supplier
    s.n_commods = Param(2)
    p = GraphParams()
    b = ReactorRequestBuilder(s, p)
    assert_raises(ValueError, b.build)
    s.n_commods = Param(1)

    # exclusive request node
    s.exclusive = BoolParam(1)
    p = GraphParams()
    b = ReactorRequestBuilder(s, p)
    b.build()
    assert_equal(len(p.excl_req_nodes[0]), 1)
    assert_equal(p.excl_req_nodes[0][0], 0)
    assert_true(p.node_excl[0])
    s.exclusive = BoolParam(-1)

    # 2 suppliers 0 connection prob
    s.connection = BoolParam(0)
    s.n_supply = Param(2)
    p = GraphParams()
    b = ReactorRequestBuilder(s, p)
    b.build()
    assert_equal(len(p.arc_pref), 1)
    s.connection = BoolParam(1)
    s.n_supply = Param(1)

    # 2 suppliers, 2 commods, 2 req nodes, 4 arcs
    s.n_commods = Param(2)
    s.n_supply = Param(2)
    s.assem_multi_commod = BoolParam(1)
    s.req_multi_commods = Param(1)
    s.sup_multi = BoolParam(1)
    p = GraphParams()
    b = ReactorRequestBuilder(s, p)
    b.build()
    assert_equal(len(p.arc_pref), 4)
    commods = b._assem_commods([0, 1])
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
    s.n_sup_constr = Param(3)
    s.n_req_constr = Param(2)
    p = GraphParams()
    b = ReactorRequestBuilder(s, p)
    b.build()
    assert_equal(len(p.constr_vals[0]), 2)
    assert_equal(len(p.constr_vals[1]), 3)
    assert_equal(len(p.node_ucaps[0][0]), 2)
    assert_equal(len(p.node_ucaps[1][0]), 3)
    s.n_sup_constr = Param(1)
    s.n_req_constr = Param(1)
