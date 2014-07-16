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

def test_sampler_builder():
    rc = RunControl(
        n_commods={'avg':[1], 'dist':[True, False]},
        n_request={'avg':[1, 3]},)
    b = SamplerBuilder(rc)

    exp = {
        (True, 1): ReactorRequestSampler(n_commods=Param(1, True), n_request=Param(1)),
        (True, 3): ReactorRequestSampler(n_commods=Param(1, True), n_request=Param(3)),
        (False, 1): ReactorRequestSampler(n_commods=Param(1, False), n_request=Param(1)),
        (False, 3): ReactorRequestSampler(n_commods=Param(1, False), n_request=Param(3)),
        }
    obs = [s for s in b.build()]
    
    assert_equal(len(exp), len(obs))
    for s in obs:
        assert_equal(exp[(s.n_commods.dist, s.n_request.avg)], s)
