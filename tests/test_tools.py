from cyclopts.tools import combine, RunControl, SamplerBuilder

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
import subprocess

exec_cmd = """cyclopts exec --db {indb} --outdb {outdb} \
--conds "{{'inst_queries':{{'ExchangeInstProperties':['n_arcs=={narcs}']}}}}"
"""

def test_combine():    
    base = os.path.dirname(os.path.abspath(__file__))
    workdir = os.path.join(base, 'files')
    orig_in = 'exp_instances.h5'
    cp_in = 'cp_instances.h5'
    tmp_out = 'tmp_out.h5'
    out1 = '1arcs.h5'
    nsoln1 = 1
    out4 = '4arcs.h5'
    nsoln4 = 2
    ninsts = 5
    tmpfiles = {out1: os.path.join(workdir, out1), 
                out4: os.path.join(workdir, out4), 
                cp_in: os.path.join(workdir, cp_in), 
                tmp_out: os.path.join(workdir, tmp_out)}
    
    # setup
    for _, f in tmpfiles.items():
        if os.path.exists(f):
            os.remove(f)
    cmd = exec_cmd.format(indb=os.path.join(workdir, orig_in), 
                          outdb=os.path.join(workdir, out1), narcs=1)
    print("executing cmd", cmd)
    subprocess.call(cmd.split(), shell=(os.name == 'nt'))
    cmd = exec_cmd.format(indb=os.path.join(workdir, orig_in), 
                          outdb=os.path.join(workdir, out4), narcs=4)
    print("executing cmd", cmd)
    subprocess.call(cmd.split(), shell=(os.name == 'nt'))
    shutil.copyfile(os.path.join(workdir, orig_in), tmpfiles[cp_in])
    
    # operations
    combine(iter([tmpfiles[cp_in], tmpfiles[out4], tmpfiles[out1]]), 
            new_file=tmpfiles[tmp_out])
    combine(iter([tmpfiles[cp_in], tmpfiles[out4], tmpfiles[out1]]))
    
    chkfiles = [tmpfiles[tmp_out], tmpfiles[cp_in]]
    for f in chkfiles:
        print("checking {0}".format(f))
        db = t.open_file(f, 'r')
        assert_equal(db.root.Instances.ExchangeInstProperties.nrows, ninsts)
        assert_equal(db.root.Instances.ExchangeInstSolutions.nrows, 
                     nsoln1 + nsoln4)
        assert_equal(db.root.Results.General.nrows, 2) # 2 runs were performed
    
    # teardown
    for _, f in tmpfiles.items():
        if os.path.exists(f):
            os.remove(f)

def test_simple_sampler_builder():
    rc = RunControl(
        n_commods=[[1], [True, False]],
        n_request= [[1, 3]],
        constr_coeff= [[0, 0.5], [1]],)
    
    b = SamplerBuilder(rc)

    # params_list = [(k, v) for k, v in b.params_it]
    # for i in range(len(params_list[0][1])):
    #     assert_equal(params_list[0][1][i].avg, i * 2 + 1)
    #     assert_equal(params_list[0][1][i].dist, None)
    # for i in range(len(params_list[1][1])):
    #     assert_equal(params_list[1][1][i].avg, 1)
    #     assert_equal(params_list[1][1][i].dist, True if i == 0 else False)
    # for i in range(len(params_list[2][1])):
    #     assert_equal(params_list[2][1][i].ub, 1)
    #     assert_equal(params_list[2][1][i].lb, 0.5 * i)
    # print("lst:", params_list)

    #samplers = b._build(rc_params)    
    #assert_equal(len(samplers), 8)
    req_exp = [1, 1, 1, 1, 3, 3, 3, 3]
    commod_exp = [True, True, False, False, True, True, False, False]
    constr_exp = [1e-10, 0.5, 0, 0.5, 0, 0.5, 0, 0.5]
    i = 0
    for s in b.build():
        assert_equal(s.n_request.avg, req_exp[i])
        assert_equal(s.n_request.dist, None)
        assert_equal(s.n_commods.avg, 1)
        #assert_equal(s.n_commods.dist, commod_exp[i])
        assert_equal(s.constr_coeff.lb, constr_exp[i])
        assert_equal(s.constr_coeff.ub, 1)
        i += 1

def test_parser():
    class TestRC():
        def __init__(self):
            self.n_request = {'avg': range(1, 5), 'dist': [True, False]}
            self.n_supply = {'avg': range(1, 5)}
            self._dict = {'n_request': self.n_request, 
                          'n_supply': self.n_supply,}

    exp_dict = {
        'n_request': [range(1, 5), [True, False]],
        'n_supply': [range(1, 5)],
        }

    b = SamplerBuilder()
    rc = TestRC()
    obs_dict = b._parse(rc)

    assert_equal(exp_dict, obs_dict)
