from cyclopts.tools import report
from cyclopts.execute import GraphParams, SolverParams, Solution, \
    ArcFlow, execute_exchange
from cyclopts.params import Incrementer, Param, BoolParam, \
    ReactorRequestSampler, ReactorRequestBuilder
import os
import nose
from nose.tools import assert_equal, assert_true, assert_false

def test_report():
    db_path = os.path.join(os.getcwd(), 'cyclopts_test_report.h5')
    
    sampler = ReactorRequestSampler()
    sp = SolverParams()
    gp = GraphParams()
    b = ReactorRequestBuilder(sampler, gp)
    b.build()
    soln = execute_exchange(gp, sp)
    for i in range(len(soln.flows)):
        f = ArcFlow(soln.flows[i:])
        print("obj:", f.id, gp.arc_pref[f.id] * f.flow)
    report(sampler, gp, sp, soln, db_path=db_path)

    # if os.path.exists(db_path):
    #     os.remove(db_path)

