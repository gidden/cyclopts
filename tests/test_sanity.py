from cyclopts.execute import ArcFlow, GraphParams, SolverParams, execute_exchange
from cyclopts.params import ReactorRequestBuilder, ReactorRequestSampler, Param
from cyclopts.dtypes import xd_arcflow

import numpy as np
import random as rnd
import operator 

import nose
from nose.tools import assert_equal, assert_true

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
            b = ReactorRequestBuilder(s)
            gparams = b.build()

            solns = [execute_exchange(gparams, solver) for solver in sparams]
            all_flows = []
            for soln in solns:
                dic = {}
                for i in range(len(soln.flows)):
                    f = ArcFlow(soln.flows[i:])
                    dic[f.id] = f.flow
                all_flows.append(dic)
            
            max_flows = [sum(dic.values()) for dic in all_flows]

            for f in max_flows:
                assert_equal(f, exp_total_flow)
            
            for i in range(len(all_flows) - 1):
                assert_equal(all_flows[i], all_flows[i+1])
