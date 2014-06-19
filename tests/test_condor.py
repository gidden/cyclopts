from __future__ import print_function

import uuid
import os
import shutil
import paramiko as pm
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
    obs = condor.gen_files(prefix, os.path.basename(db), instids, solvers, 
                           subfile=subfile, max_time=max_time)   
    
    exp = ['0.sub', '1.sub', 'run.sh', subfile]
    exp = [os.path.join(prefix, x) for x in exp]
    assert_equal(set(exp), set(obs))
 
    obs = os.listdir(prefix)
    assert_equal(len(exp), len(obs))
    for f in exp:
        assert_true(os.path.basename(f) in obs)

    if os.path.exists(prefix):
        shutil.rmtree(prefix)    

def test_get_files():
    user = 'gidden'
    host = 'submit-1.chtc.wisc.edu'
    ssh = pm.SSHClient()
    ssh.set_missing_host_key_policy(pm.AutoAddPolicy())

    localbase = os.path.dirname(os.path.abspath(__file__))
    remotebase = condor.batlab_base_dir_template.format(user=user)
    tmpdir = 'tmp_{0}'.format(uuid.uuid4())
    localdir = os.path.join(localbase, tmpdir)
    remotedir = '{0}/{1}'.format(remotebase, tmpdir)

    os.makedirs(localdir)
    
    ssh.connect(host, username=user, password=None)    
    tstfiles = ['tmp_test_file', 'tmp_other_file']
    for f in tstfiles:
        cmd = "mkdir -p {0} && touch {0}/{1}".format(remotedir, f)
        ssh.exec_command(cmd)
    files = condor.get_files(ssh, remotedir, localdir, 'tmp_*')
    cmd = "rm -rf {0}".format(remotedir)
    ssh.exec_command(cmd)
    ssh.close()

    assert_equal(set(files), set(['./{0}'.format(f) for f in tstfiles]))
    assert_equal(set(os.listdir(localdir)), set(tstfiles))
    
    shutil.rmtree(localdir)
