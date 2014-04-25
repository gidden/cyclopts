from cyclopts.tools import report, combine, SamplerBuilder

from cyclopts.execute import GraphParams, SolverParams, Solution, \
    ArcFlow, execute_exchange
from cyclopts.params import Incrementer, Param, BoolParam, \
    ReactorRequestSampler, ReactorRequestBuilder

import operator
import shutil
import os
import uuid
import nose
import tables as t
from functools import reduce
from nose.tools import assert_equal, assert_true, assert_false

def test_report():
    db_path = os.path.join(os.getcwd(), str(uuid.uuid4()) + '.h5')
    
    sampler = ReactorRequestSampler()
    sp = SolverParams()
    gp = GraphParams()
    b = ReactorRequestBuilder(sampler, gp)
    b.build()
    soln = execute_exchange(gp, sp)
    for i in range(len(soln.flows)):
        f = ArcFlow(soln.flows[i:])
        print("obj:", f.id, f.flow / gp.arc_pref[f.id])
    report(sampler, gp, sp, soln, db_path=db_path)

    if os.path.exists(db_path):
        os.remove(db_path)

def test_combine():    
    db1 = '994c5721-311d-46f3-8b7d-742beeaa9ec1.h5'
    db2 = 'e5b781e6-fb86-4099-a46b-f36370bf8af4.h5'
    db1 = os.path.join(os.getcwd(), 'dbs', db1)
    db2 = os.path.join(os.getcwd(), 'dbs', db2)
    
    new_file = os.path.join(os.getcwd(), 'dbs', 'combine.h5')
    copy_file = os.path.join(os.getcwd(), 'dbs', 'copy.h5')
    tmps = [new_file, copy_file]
    for tmp in tmps:
        if os.path.exists(tmp):
            os.remove(tmp)
    shutil.copyfile(db1, copy_file)
    
    combine([db1, db2], new_file=new_file)
    f1 = t.open_file(db1, 'r')
    f2 = t.open_file(db2, 'r')
    test = t.open_file(new_file, 'r')
    test_ids = [x['sim_id'] for x in test.root.solution.iterrows()]
    f1_ids = [x['sim_id'] for x in f1.root.solution.iterrows()]
    f2_ids = [x['sim_id'] for x in f2.root.solution.iterrows()]
    assert_equal(test_ids[0], f1_ids[0])
    assert_equal(test_ids[0], f1_ids[0])
    assert_equal(test_ids[1], f2_ids[0])
    assert_equal(len(test_ids), 2)
    assert_equal(len(f1_ids), 1)
    assert_equal(len(f2_ids), 1)
    test.close()
    f2.close()
    f1.close()

    combine([copy_file, db2])
    f1 = t.open_file(db1, 'r')
    f2 = t.open_file(db2, 'r')
    test = t.open_file(copy_file, 'r')
    test_ids = [x['sim_id'] for x in test.root.solution.iterrows()]
    f1_ids = [x['sim_id'] for x in f1.root.solution.iterrows()]
    f2_ids = [x['sim_id'] for x in f2.root.solution.iterrows()]
    assert_equal(test_ids[0], f1_ids[0])
    assert_equal(test_ids[0], f1_ids[0])
    assert_equal(test_ids[1], f2_ids[0])
    assert_equal(len(test_ids), 2)
    assert_equal(len(f1_ids), 1)
    assert_equal(len(f2_ids), 1)
    test.close()
    f2.close()
    f1.close()
    
    for tmp in tmps:
        if os.path.exists(tmp):
            os.remove(tmp)

def test_simple_sampler_builder():
    rc_params = {
        'n_commods': [[1], [True, False]],
        'n_request': [[1, 3]],
        'constr_coeff': [[0, 0.5], [1]],
        }

    b = SamplerBuilder()

    params_list = b._constr_params(rc_params)
    for i in range(len(params_list[0][1])):
        assert_equal(params_list[0][1][i].avg, i * 2 + 1)
        assert_equal(params_list[0][1][i].dist, None)
    for i in range(len(params_list[1][1])):
        assert_equal(params_list[1][1][i].avg, 1)
        assert_equal(params_list[1][1][i].dist, True if i == 0 else False)
    for i in range(len(params_list[2][1])):
        assert_equal(params_list[2][1][i].ub, 1)
        assert_equal(params_list[2][1][i].lb, 0.5 * i)
    print("lst:", params_list)

    samplers = b._build(rc_params)    
    assert_equal(len(samplers), 8)
    req_exp = [1, 1, 1, 1, 3, 3, 3, 3]
    commod_exp = [True, True, False, False, True, True, False, False]
    constr_exp = [0, 0.5, 0, 0.5, 0, 0.5, 0, 0.5]
    for i in range(len(samplers)):
        print(samplers[i].n_request)
        assert_equal(samplers[i].n_request.avg, req_exp[i])
        assert_equal(samplers[i].n_request.dist, None)
        assert_equal(samplers[i].n_commods.avg, 1)
        assert_equal(samplers[i].n_commods.dist, commod_exp[i])
        assert_equal(samplers[i].constr_coeff.lb, constr_exp[i])
        assert_equal(samplers[i].constr_coeff.ub, 1)

def test_parser():
    class TestRC():
        def __init__(self):
            self.n_request = {'avg': range(1, 5), 'dist': [True, False]}
            self.n_supply = {'avg': range(1, 5)}

    exp_dict = {
        'n_request': [range(1, 5), [True, False]],
        'n_supply': [range(1, 5)],
        }

    b = SamplerBuilder()
    rc = TestRC()
    obs_dict = b._parse(rc)

    assert_equal(exp_dict, obs_dict)
