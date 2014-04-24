from cyclopts.execute import ArcFlow, GraphParams, SolverParams, execute_exchange
from cyclopts.params import ReactorRequestBuilder, ReactorRequestSampler, \
    Param, SupConstrParam
from cyclopts.dtypes import xd_arcflow

import numpy as np
import random as rnd
import operator 

import nose
from nose.tools import assert_equal, assert_almost_equal, assert_true

def test_rr_sanity():
    solvers = ['greedy', 'cbc', 'clp']
    sparams = [SolverParams(solver) for solver in solvers]
    n_req_max = 100
    n_sup_max = 100
    
    for nreq in range(1, n_req_max, 49):
        for nsup in range(1, n_sup_max, 49):
            print("testing", "nreq:", nreq, "nsup:", nsup)
            exp_total_flow = nreq
            s = ReactorRequestSampler()
            s.n_request = Param(nreq)
            s.n_supply = Param(nsup)
            s.sup_constr_val = SupConstrParam(1.0 / nsup)
            b = ReactorRequestBuilder(s)
            gparams = b.build()

            solns = [execute_exchange(gparams, solver) for solver in sparams]

            all_flows = [{ArcFlow(soln.flows[i:]).id: ArcFlow(soln.flows[i:]).flow \
                              for i in range(len(soln.flows))} for soln in solns]
            max_flows = [sum(dic.values()) for dic in all_flows]
            objs = [sum([flow / gparams.arc_pref[id] for id, flow in flows.items()]) \
                        for flows in all_flows]
            for f in max_flows:
                assert_almost_equal(f, exp_total_flow)
            
            max_obj = max(objs)
            objs = [obj / max_obj for obj in objs]
            for i in range(len(objs) - 1):
                assert_almost_equal(objs[i], objs[i+1], places=2)
