from cyclopts.tools import Incrementer, combine, RunControl, SamplerBuilder

from cyclopts.params import Param, BoolParam, \
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
import uuid

from cyclopts import exchange_family
from cyclopts import tools

exec_cmd = """cyclopts exec --db {indb} --outdb {outdb} \
--conds "{{'inst_queries':['n_arcs=={narcs}']}}" \
 --family_class ResourceExchange --family_module cyclopts.exchange_family
"""

def test_incr():
    i = Incrementer()
    assert_equal(i.next(), 0)
    i = Incrementer(5)
    assert_equal(i.next(), 5)
    assert_equal(i.next(), 6)

def test_combine():    
    base = os.path.dirname(os.path.abspath(__file__))
    workdir = os.path.join(base, 'files')
    orig_in = 'obs_valid_in.h5'
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
        path = '/Family/ResourceExchange/ExchangeInstProperties'
        assert_equal(db.get_node(path).nrows, ninsts)
        path = '/Family/ResourceExchange/ExchangeInstSolutions'
        assert_equal(db.get_node(path).nrows, nsoln1 + nsoln4)
        path = '/Results'
        assert_equal(db.get_node(path).nrows, 2) # 2 runs were performed
    
    # teardown
    for _, f in tmpfiles.items():
        if os.path.exists(f):
            os.remove(f)

def test_get_obj():    
    class Args(object):
        def __init__(self, package=None, module='cyclopts.exchange_family', 
                     cl='ResourceExchange'):
            self.family_package = package
            self.family_module = module
            self.family_class = cl
    
    exp_obj = exchange_family.ResourceExchange
    kind = 'family'

    args = Args()
    rc = Args(None, None, None)
    assert_true(exp_obj, tools.get_obj(kind=kind, rc=rc, args=args))

    args = Args(None, None, None)
    rc = Args()
    assert_true(exp_obj, tools.get_obj(kind=kind, rc=rc, args=args))

    args = Args(None, 'cyclopts.exchange_family', None)
    rc = Args()
    assert_true(exp_obj, tools.get_obj(kind=kind, rc=rc, args=args))

def test_collect_instids():
    base = os.path.dirname(os.path.abspath(__file__))
    fpth = os.path.join(base, 'files', 'obs_valid_in.h5')
    h5file = t.open_file(fpth, 'r')
    path = '/Family/ResourceExchange/ExchangeInstProperties'
    
    # test all
    vals = [x['instid'] for x in h5file.get_node(path).iterrows()]
    vals = [x + '\0' if len(x) == 15 else x for x in vals]
    exp_uuids = [uuid.UUID(bytes=x) for x in vals]
    obs_uuids = tools.collect_instids(h5file, path)    
    assert_equal(set(exp_uuids), obs_uuids)

    # test subset
    instids = [uuid.UUID(bytes=x).hex for x in vals[:-2]]
    exp_uuids = exp_uuids[:-2]
    obs_uuids = tools.collect_instids(h5file, path, instids=instids)    
    assert_equal(set(exp_uuids), obs_uuids)

    # test rc
    vals = [x['instid'] for x in h5file.get_node(path).iterrows() \
                if x['n_arcs'] == 2 and x['n_u_grps'] == 2]
    vals = [x + '\0' if len(x) == 15 else x for x in vals]
    exp_uuids = [uuid.UUID(bytes=x) for x in vals]
    rc = RunControl(inst_queries=['n_arcs == 2', '&', 'n_u_grps == 2'])
    obs_uuids = tools.collect_instids(h5file, path, rc)    
    assert_equal(set(exp_uuids), obs_uuids)
    
    # test combined
    obs_uuids = tools.collect_instids(h5file, path, rc=rc, instids=[instids[0]])    
    exp_uuids += [uuid.UUID(instids[0])]
    assert_equal(set(exp_uuids), obs_uuids)
    
    h5file.close()    

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
