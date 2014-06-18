from __future__ import print_function

import uuid
import os
import shutil

from cyclopts import condor
from cyclopts import main

from test_main import exp_uuid_arcs 

import nose
from nose.tools import assert_equal, assert_true

def test_file_gen():
    base = os.path.dirname(os.path.abspath(__file__))
    db = os.path.join(base, 'files', 'exp_instances.h5')
    prefix=os.path.join(base, 'tmp_{0}'.format(uuid.uuid4()))
    instids = [x[0] for x in exp_uuid_arcs[:2]] # 2 ids
    solvers = ['s1', 's2']
    subfile = 'tst.sub'
    max_time = 5
    condor.gen_files(prefix, db, instids, solvers, subfile=subfile, 
                     max_time=max_time)   
    
    exp = ['0.sub', '1.sub', 'run.sh', subfile, os.path.basename(db)]
    obs = os.listdir(prefix)
    assert_equal(len(exp), len(obs))
    for f in exp:
        assert_true(f in obs)

    if os.path.exists(prefix):
        shutil.rmtree(prefix)    
