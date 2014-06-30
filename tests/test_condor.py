from __future__ import print_function

import uuid
import os
import shutil
import paramiko as pm
import warnings

from cyclopts import condor
from cyclopts import main
from cyclopts import tools

from test_main import exp_uuid_arcs 

import nose
from nose.tools import assert_equal, assert_true

def test_file_gen():
    base = os.path.dirname(os.path.abspath(__file__))
    db = os.path.join(base, 'files', 'exp_instances.h5')
    prefix=os.path.join(base, 'tmp_{0}'.format(uuid.uuid4()))
    instids = [x[0] for x in exp_uuid_arcs()[:2]] # 2 ids
    solvers = ['s1', 's2']
    subfile = 'tst.sub'
    max_time = 5
    obs = condor.gen_dag_tar(prefix, db, instids, solvers, '.', 
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
    host = 'submit-3.chtc.wisc.edu'

    localbase = os.path.dirname(os.path.abspath(__file__))
    remotebase = condor.batlab_base_dir_template.format(user=user)
    tmpdir = 'tmp_{0}'.format(uuid.uuid4())
    localdir = os.path.join(localbase, tmpdir)
    remotedir = '/'.join([remotebase, tmpdir])
    
    client = pm.SSHClient()
    client.set_missing_host_key_policy(pm.AutoAddPolicy())
    can_connect, keyfile = tools.ssh_test_connect(client, host, user, auth=False)
    if not can_connect:
        warnings.warn(("This test requires your public key to be added to"
                       " {0}@{1}'s authorized keys.").format(user, host))
        return
    
    os.makedirs(localdir)
    prefix='tmp_'
    tstfiles = [prefix + 'test_file', prefix + 'other_file']
    touchline = " ".join("/".join([remotedir, f]) for f in tstfiles)
    cmd = "mkdir -p {0} && touch {1}".format(remotedir, touchline)
    client.connect(host, username=user, key_filename=keyfile)
    client.exec_command(cmd)
    condor._wait_till_found(client, '/'.join([remotedir, tstfiles[-1]]))
    nfiles = condor.get_files(client, remotedir, localdir, prefix + '*')
    client.close()
    
    assert_equal(set(os.listdir(localdir)), set(tstfiles))
    
    client.connect(host, username=user, key_filename=keyfile)
    cmd = "rm -rf {0}".format(remotedir)
    client.exec_command(cmd)
    client.close()
        
    shutil.rmtree(localdir)
