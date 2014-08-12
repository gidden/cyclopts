from __future__ import print_function

import uuid
import os
import shutil
import paramiko as pm
import warnings
import tarfile
import tables as t

from cyclopts.condor import dag
from cyclopts.condor import queue
from cyclopts.condor import utils
from cyclopts import main
from cyclopts import tools

import nose
from nose.tools import assert_equal, assert_true

from utils import timeout, TimeoutError

"""this is a print out of uid hexs and their number of arcs taken from
cyclopts/tests/files/obs_valid_in.h5 on 6/15/14 via

.. code-block::

  import tables as t
  h5f = t.open_file('cyclopts/tests/files/obs_valid_in.h5', 'r')
  h5n = h5f.root.Instances.ExchangeInstProperties
  for row in h5n.iterrows():
    print(uuid.UUID(bytes=row['instid']).hex, row['n_arcs'])

"""
_exp_uuid_arcs = []
def exp_uuid_arcs():
    global _exp_uuid_arcs    
    if len(_exp_uuid_arcs) == 0:
        base = os.path.dirname(os.path.abspath(__file__))
        pth = os.path.join(base, 'files', 'obs_valid_in.h5')
        h5file = t.open_file(pth, 'r')
        path = '/Family/ResourceExchange/ExchangeInstProperties'
        tbl = h5file.get_node(path)
        _exp_uuid_arcs = [(uuid.UUID(bytes=row['instid']).hex, row['n_arcs']) \
                              for row in tbl.iterrows()]
        h5file.close()
    return _exp_uuid_arcs

def test_gen_dag_tar():
    base = os.path.dirname(os.path.abspath(__file__))
    db = os.path.join(base, 'files', 'obs_valid_in.h5')
    prefix='tmp_{0}'.format(uuid.uuid4())
    instids = [x[0] for x in exp_uuid_arcs()[:2]] # 2 ids
    solvers = ['s1', 's2']
    
    dag.gen_tar(prefix, db, instids, solvers)   
    
    if os.path.exists(prefix):
        shutil.rmtree(prefix)    

    exp = ['0.sub', '1.sub', 'run.sh', 'dag.sub', 'obs_valid_in.h5']
    tarname = '{0}.tar.gz'.format(prefix)
    obs = [] 
    with tarfile.open(tarname, 'r:gz') as tar:
        for f in tar.getnames():
            s = f.split('/')
            assert_equal(len(s), 2)
            assert_equal(s[0], prefix)
            obs += [s[1]]
    assert_equal(len(exp), len(obs))
    assert_equal(set(exp), set(obs))
    os.remove(tarname)

def test_gen_q_tar():
    base = os.path.dirname(os.path.abspath(__file__))
    db = os.path.join(base, 'files', 'obs_valid_in.h5')
    prefix='tmp_{0}'.format(uuid.uuid4())
    instids = [x[0] for x in exp_uuid_arcs()[:2]] # 2 ids
    solvers = ['s1', 's2']
    
    queue.gen_tar(prefix, db, instids, solvers)   
    
    if os.path.exists(prefix):
        shutil.rmtree(prefix)    

    exp = ['uuids', 'launch_master.py', 'run.sh', 'obs_valid_in.h5']
    tarname = '{0}.tar.gz'.format(prefix)
    obs = []
    with tarfile.open(tarname, 'r:gz') as tar:
        for f in tar.getnames():
            s = f.split('/')
            assert_equal(len(s), 2)
            assert_equal(s[0], prefix)
            obs += [s[1]]
    assert_equal(len(exp), len(obs))
    assert_equal(set(exp), set(obs))
    os.remove(tarname)
    
@timeout()
def test_get_files():
    user = 'gidden'
    host = 'submit-3.chtc.wisc.edu'

    localbase = os.path.dirname(os.path.abspath(__file__))
    remotebase = utils.batlab_base_dir_template.format(user=user)
    tmpdir = 'tmp_{0}'.format(uuid.uuid4())
    localdir = os.path.join(localbase, tmpdir)
    remotedir = '/'.join([remotebase, tmpdir])

    try:
        client = pm.SSHClient()
        client.set_missing_host_key_policy(pm.AutoAddPolicy())
        can_connect, keyfile, pw = tools.ssh_test_connect(client, host, user, 
                                                          auth=False)
    except TimeoutError:
        warnings.warn('could not connect via ssh to {0}@{1}'.format(user, host))
        return
    
    os.makedirs(localdir)
    prefix='tmp_'
    tstfiles = [prefix + 'test_file', prefix + 'other_file']
    touchline = " ".join("/".join([remotedir, f]) for f in tstfiles)
    cmd = "mkdir -p {0} && touch {1}".format(remotedir, touchline)
    
    try:
        client.connect(host, username=user, key_filename=keyfile)
        stdin, stdout, stderr = utils.exec_remote_cmd(client, cmd, verbose=True)
        print("getting", remotedir)
        nfiles = utils.get_files(client, remotedir, localdir, prefix + '*')
        client.close()
    except TimeoutError:
        warnings.warn('could not connect via ssh to {0}@{1}'.format(user, host))
        return
    
    assert_equal(set(os.listdir(localdir)), set(tstfiles))
    
    client.connect(host, username=user, key_filename=keyfile)
    cmd = "rm -rf {0}".format(remotedir)
    stdin, stdout, stderr = utils.exec_remote_cmd(client, cmd, verbose=True)
    client.close()
        
    shutil.rmtree(localdir)
