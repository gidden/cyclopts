from __future__ import print_function

from cyclopts.execute import ArcFlow, ExecParams, execute_exchange
from cyclopts.dtypes import xd_arcflow

import numpy as np
import random as rnd

import nose
from nose.tools import assert_equal, assert_true

def test_null():
    params = ExecParams()
    obs = execute_exchange(params)
    assert_true(np.empty(obs))

# this is like test case 3 from exchange_test_cases in Cyclus
# Case 3:
# 2 suppliers (2 nodes) with capacity, c1 & c2
# 1 requester (1 node) with request quantity, q
# requester pref for s1 := p1
# requester pref for s2 := p2
# flow from s1 -> r := f1
# flow from s2 -> r := f2
def test_simple():
    params = ExecParams()
    reqs = [0]
    sups = [1, 2]
    u_nodes = [0]
    v_nodes = [1, 2]
    arcs = [0, 1]
    
    params.arc_to_unode = {0: 0, 1: 0}
    params.arc_to_vnode = {0: 1, 1: 2}
    
    params.u_nodes_per_req = {0: np.array(u_nodes)}
    params.v_nodes_per_sup = {1: np.array([v_nodes[0]]),
                              2: np.array([v_nodes[1]]),}

    params.req_qty = {0: 5}
    params.node_qty = {0: 5}

    params.node_excl = {0: False, 1: False, 2: False}
    params.excl_req_nodes = {0: np.array(np.array([], dtype='int'))}
    params.excl_sup_nodes = {1: np.array([], dtype='int')}

    params.node_ucaps = {0: {0: np.array([], dtype='float'), 
                             1: np.array([], dtype='float')},
                         1: {0: np.array([1.0], dtype='float')},
                         2: {1: np.array([1.0], dtype='float')},}

    params.constr_vals = {0: np.array([], dtype='float'), 
                          1: np.array([3], dtype='float'), 
                          2: np.array([params.req_qty[0] - 3 + 0.1], 
                                      dtype='float')}
    print("constr vals", params.constr_vals)

    params.def_constr_coeff = {0: 1}
    
    # pref first to second
    params.arc_pref = {0: 0.75, 1: 0.25}

    obs = execute_exchange(params)
    exp = {0: params.constr_vals[1][0], 
           1: params.req_qty[0] - params.constr_vals[1][0]}    
    print("exp", exp)
    print("nobs", len(obs))
    for i in range(len(obs)):
        ob = ArcFlow(obs[i:])
        print("obs id and flow", ob.id, ob.flow)
    for i in range(len(obs)):
        ob = ArcFlow(obs[i:])
        assert_equal(exp[ob.id], ob.flow)

    # pref second to first
    params.arc_pref = {0: 0.25, 1: 0.75}

    obs = execute_exchange(params)
    exp = {1: params.constr_vals[2][0],
           0: params.req_qty[0] - params.constr_vals[2][0]}    
    print("exp", exp)
    print("nobs", len(obs))
    for i in range(len(obs)):
        ob = ArcFlow(obs[i:])
        print("obs id and flow", ob.id, ob.flow)
    for i in range(len(obs)):
        ob = ArcFlow(obs[i:])
        assert_equal(exp[ob.id], ob.flow)
