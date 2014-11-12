from cyclopts.tools import Incrementer, combine, RunControl
from cyclopts.params import Param, BoolParam

import operator
import shutil
import os
import uuid
import nose
import tables as t
from functools import reduce
from nose.tools import assert_equal, assert_true, assert_false, assert_raises
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

# this can be cleaned up in the future...
class TestCombine:

    def _cleanup(self):
        for _, f in self.tmpfiles.items():
            if os.path.exists(f):
                os.remove(f)

    def setup(self):
        base = os.path.dirname(os.path.abspath(__file__))
        self.workdir = os.path.join(base, 'files')
        self.orig_in = 'obs_valid_in.h5'
        self.cp_in = 'cp_instances.h5'
        self.tmp_out = 'tmp_out.h5'
        self.out1 = '1arcs.h5'
        self.nsoln1 = 1
        self.out4 = '4arcs.h5'
        self.nsoln4 = 4
        self.ninsts = 4
        self.tmpfiles = {self.out1: os.path.join(self.workdir, self.out1), 
                         self.out4: os.path.join(self.workdir, self.out4), 
                         self.cp_in: os.path.join(self.workdir, self.cp_in), 
                         self.tmp_out: os.path.join(self.workdir, self.tmp_out)}
        self._cleanup()
        self.passed = False
        
    def teardown(self):
        # teardown
        if self.passed:
            self._cleanup()

    def test_combine(self):    
        cmd = exec_cmd.format(indb=os.path.join(self.workdir, self.orig_in), 
                              outdb=os.path.join(self.workdir, self.out1), narcs=1)
        print("executing cmd", cmd)
        subprocess.call(cmd.split(), shell=(os.name == 'nt'))
        cmd = exec_cmd.format(indb=os.path.join(self.workdir, self.orig_in), 
                              outdb=os.path.join(self.workdir, self.out4), narcs=4)
        print("executing cmd", cmd)
        subprocess.call(cmd.split(), shell=(os.name == 'nt'))
        shutil.copyfile(os.path.join(self.workdir, self.orig_in), 
                        self.tmpfiles[self.cp_in])
        
        # operations
        combine(iter([self.tmpfiles[self.cp_in], self.tmpfiles[self.out4], 
                      self.tmpfiles[self.out1]]), 
                new_file=self.tmpfiles[self.tmp_out])
        combine(iter([self.tmpfiles[self.cp_in], self.tmpfiles[self.out4], 
                      self.tmpfiles[self.out1]]))
    
        chkfiles = [self.tmpfiles[self.tmp_out], self.tmpfiles[self.cp_in]]
        for f in chkfiles:
            print("checking {0}".format(f))
            db = t.open_file(f, 'r')
            path = '/Results'
            assert_equal(db.get_node(path).nrows, 2) # 2 runs were performed
            path = '/Family/ResourceExchange/ExchangeInstProperties'
            assert_equal(db.get_node(path).nrows, self.ninsts)
            path = '/Family/ResourceExchange/ExchangeInstSolutions'
            n = 0
            for tbl in db.get_node(path)._f_walknodes(classname='Table'):
                n += tbl.nrows
            assert_equal(n, self.nsoln1 + self.nsoln4)
            db.close()
        self.passed = True
        
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
    assert_true(exp_obj, tools.get_obj(kind=kind, rcs=rc, args=args))

    args = Args(None, None, None)
    rc = Args()
    assert_true(exp_obj, tools.get_obj(kind=kind, rcs=rc, args=args))

    args = Args(None, 'cyclopts.exchange_family', None)
    rc = Args()
    assert_true(exp_obj, tools.get_obj(kind=kind, rcs=rc, args=args))

    args = Args(None, None, None)
    rc1 = Args(None, None, None)
    rc = Args()
    assert_true(exp_obj, tools.get_obj(kind=kind, rcs=[rc1, rc], args=args))

    rc = Args(None, None, None)
    assert_raises(RuntimeError, tools.get_obj, kind=kind, rcs=rc)

    rc = Args(None, 'cyclopts.exchange_family', 'blah')
    assert_raises(RuntimeError, tools.get_obj, kind=kind, rcs=rc)

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
    instids = [uuid.UUID(bytes=x) for x in vals[:-2]]
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
    exp_uuids += [instids[0]]
    assert_equal(set(exp_uuids), obs_uuids)
    
    h5file.close()    

def test_n_permutations():
    x = "foo"
    assert_equal(1, tools.n_permutations(x))
    
    x = 42
    assert_equal(1, tools.n_permutations(x))
    
    x = ["foo", 42]
    assert_equal(2, tools.n_permutations(x))
    
    x = [[1, 2]]
    assert_equal(2, tools.n_permutations(x))
    
    x = [[1, 2], [2, 3]]
    assert_equal(2, tools.n_permutations(x, recurse=False))
    
    x = {"foo": [[1, 2]], "bar": [[1, 2]]}
    assert_equal(4, tools.n_permutations(x))

    x = {'foo': [[1, 2]], 'bar': [[1, 2]], 'baz': [[1, 2]]}
    assert_equal(2 ** 3, tools.n_permutations(x))

    x = {'foo': [[1, 2], [1, 3]], 'bar': [[1, 2]], 'baz': [[1, 2]]}
    assert_equal(2 ** 4, tools.n_permutations(x))
    assert_equal(2 ** 3, tools.n_permutations(x, iter_keys=["foo"]))
    
    x = {"foo": range(10), "bar": ["42", 42]}
    assert_equal(20, tools.n_permutations(x))
    assert_equal(2, tools.n_permutations(x, iter_keys=["foo"]))

    x = {"foo": {"foobar": range(10), "foobaz": range(5)}, "bar": ["42", 42]}
    assert_equal(100, tools.n_permutations(x))

    x = {"foo": [range(10), range(5)], "bar": ["42", 42]}
    assert_equal(100, tools.n_permutations(x))

def test_expand_args():
    args = [[0, 1, 2], [0.5, 1.0], [0.2]]
    
    exp = set([(0, 0.5, 0.2), (1, 0.5, 0.2), (2, 0.5, 0.2),
               (0, 1.0, 0.2), (1, 1.0, 0.2), (2, 1.0, 0.2)])
    obs = set([x for x in tools.expand_args(args)])
    assert_equal(obs, exp)
