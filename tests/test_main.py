from cyclopts import main
from cyclopts import tools
from cyclopts import condor

from cyclopts.random_request_species import RandomRequest

import os
import shutil
import tables as t
import uuid
import subprocess
import numpy as np
from numpy.testing import assert_array_equal
import paramiko as pm
import warnings

import nose
from nose.tools import assert_equal, assert_true

from utils import timeout, TimeoutError

"""this is a print out of uid hexs and their number of arcs taken from
cyclopts/tests/files/exp_instances.h5 on 6/15/14 via

.. code-block::

  import tables as t
  h5f = t.open_file('cyclopts/tests/files/exp_instances.h5', 'r')
  h5n = h5f.root.Instances.ExchangeInstProperties
  for row in h5n.iterrows():
    print(uuid.UUID(bytes=row['instid']).hex, row['n_arcs'])

"""
_exp_uuid_arcs = []
def exp_uuid_arcs():
    global _exp_uuid_arcs    
    if len(_exp_uuid_arcs) == 0:
        base = os.path.dirname(os.path.abspath(__file__))
        pth = os.path.join(base, 'files', 'exp_instances.h5')
        h5file = t.open_file(pth, 'r')
        tbl = h5file.root.Instances.ExchangeInstProperties
        _exp_uuid_arcs = [(uuid.UUID(bytes=row['instid']).hex, row['n_arcs']) \
                              for row in tbl.iterrows()]
        h5file.close()
    return _exp_uuid_arcs

def test_instids():
    base = os.path.dirname(os.path.abspath(__file__))
    pth = os.path.join(base, 'files', 'exp_instances.h5')
    h5file = t.open_file(pth, 'r')
    h5node = h5file.root.Instances
    
    rc = tools.RunControl()
    obs = main.collect_instids(h5node=h5node, rc=rc)
    exp = exp_uuid_arcs()
    exp = set(uuid.UUID(x[0]).bytes for x in exp)
    assert_equal(len(exp), len(obs))
    assert_equal(exp, obs)
    
    exp_uuid_hex = exp_uuid_arcs()[0][0]
    rc = tools.RunControl()
    rc._update({'inst_ids': [exp_uuid_hex]})
    print("rc:", rc)
    obs = main.collect_instids(h5node=h5node, rc=rc)
    exp = set([uuid.UUID(exp_uuid_hex).bytes])
    assert_equal(len(exp), len(obs))
    assert_equal(exp, obs)

    bounds = (3, 12)
    conds = ['n_arcs > {0}'.format(bounds[0]), '&', 
             'n_arcs < {0}'.format(bounds[1])]
    rc = tools.RunControl()
    rc._update({'inst_queries': {'ExchangeInstProperties': conds}})
    obs = main.collect_instids(h5node=h5node, rc=rc)
    exp = set(uuid.UUID(x[0]).bytes \
                  for x in exp_uuid_arcs() \
                  if x[1] > bounds[0] and x[1] < bounds[1])
    assert_equal(exp, obs)
    h5file.close()

def test_exec():
    infile = 'obs_valid_in.h5'
    ninst = 5
    
    base = os.path.dirname(os.path.abspath(__file__))
    db = os.path.join(base, "tmp_{0}.h5".format(str(uuid.uuid4())))
    shutil.copy(os.path.join(base, 'files', infile), db)
    solvers = "greedy clp cbc"
    cmd = ("cyclopts exec --db={0} --family_class ResourceExchange "
           "--family_module cyclopts.exchange_family "
           "--solvers {1}").format(db, solvers)
    assert_equal(0, subprocess.call(cmd.split(), shell=(os.name == 'nt')))
    
    h5file = t.open_file(db, 'r')
    path = '/Results'
    h5node = h5file.get_node(path)
    assert_equal(h5node.nrows, ninst * len(solvers.split()))
    for row in h5node.iterrows():
        assert_true(row['objective'] > 0)
        assert_true(row['time'] > 0)
    h5file.close()
    
    if os.path.exists(db):
        os.remove(db)

def test_convert():
    base = os.path.dirname(os.path.abspath(__file__))
    rc = os.path.join(base, 'files', 'obs_valid.rc')    
    db = os.path.join(base, "tmp_{0}.h5".format(str(uuid.uuid4())))

    ninst = 2
    nvalid = 5 # visual confirmation of obs_valid.rc

    cmd = "cyclopts convert --rc {0} --db {1} -n {2}".format(rc, db, ninst)
    assert_equal(0, subprocess.call(cmd.split(), shell=(os.name == 'nt')))
    h5file = t.open_file(db, 'r')
    
    sp = RandomRequest()
    path = '/'.join(['', 'Species', sp.name])
    h5node = h5file.get_node(path, sp.tbl_name)
    assert_equal(h5node.nrows, nvalid)
    
    fam = sp.family
    path = '/'.join(['', 'Family', fam.name])
    h5node = h5file.get_node(path, 'ExchangeInstProperties') # a little hacky...
    assert_equal(h5node.nrows, nvalid * ninst)

    if os.path.exists(db):
        os.remove(db)

def test_combine():
    localbase = os.path.dirname(os.path.abspath(__file__))
    localdir = 'example_run'
    localpath = os.path.join(localbase, 'files', localdir)
    
    exp_files = ['0_out.h5', '1_out.h5']
    exp_total = 0
    for f in exp_files:
        h5file = t.open_file(os.path.join(localpath, f), 'r')
        h5node = h5file.root.Results.General
        exp_total += h5node.nrows
        h5file.close()

    outdb = os.path.join(localbase, '.tmp_{0}.h5'.format(uuid.uuid4()))
    cmd = "cyclopts combine --files {0} --outdb {1}".format(
        " ".join([os.path.join(localpath, f) for f in exp_files]), outdb)
    rtn = subprocess.call(cmd.split(), shell=(os.name == 'nt'))
    assert_equal(0, rtn)

    h5file = t.open_file(outdb, 'r')
    h5node = h5file.root.Results.General
    assert_equal(h5node.nrows, exp_total)
    h5file.close()
    os.remove(outdb)

@timeout()
def test_collect():
    user = 'gidden'
    host = 'submit-3.chtc.wisc.edu'
    try: 
        client = pm.SSHClient()
        client.set_missing_host_key_policy(pm.AutoAddPolicy())
        can_connect, keyfile, pw = tools.ssh_test_connect(client, host, user, 
                                                          auth=False)
    except TimeoutError:
        warnings.warn('could not connect via ssh to {0}@{1}'.format(user, host))
        return
    
    localbase = os.path.dirname(os.path.abspath(__file__))
    localdir = 'example_run'
    localpath = os.path.join(localbase, 'files', localdir)
    
    exp_files = ['0_out.h5', '1_out.h5']
    exp_total = 0
    for f in exp_files:
        h5file = t.open_file(os.path.join(localpath, f), 'r')
        h5node = h5file.root.Results.General
        exp_total += h5node.nrows
        h5file.close()

    remotebase = condor.utils.batlab_base_dir_template.format(user=user)
    remotedir = '.tmp_{0}'.format(uuid.uuid4()) 
    remotepath = '/'.join([remotebase, tools.cyclopts_remote_run_dir, 
                           remotedir])
    

    client.connect(host, username=user, key_filename=keyfile)
    ftp = client.open_sftp()
    print("making remote directory", remotepath)
    ftp.mkdir(remotepath)
    for f in os.listdir(localpath):
        ftp.put(os.path.join(localpath, f), '/'.join([remotepath, f]))
    ftp.close()

    tmppath = os.path.join(localbase, '.tmp_{0}'.format(uuid.uuid4()))
    outdb = os.path.join(tmppath, 'test_collect_out.h5')
    cmd = "cyclopts condor-collect -l {0} -d {1} --outdb {2}".format(
        tmppath, remotedir, outdb)
    rtn = subprocess.call(cmd.split(), shell=(os.name == 'nt'))
    assert_equal(0, rtn)
    cmd = "rm -rf {0}".format(remotepath)
    client.exec_command(cmd)
    client.close()

    h5file = t.open_file(outdb, 'r')
    h5node = h5file.root.Results.General
    assert_equal(h5node.nrows, exp_total)
    h5file.close()

    shutil.rmtree(tmppath)
    

#
# This was a first attempt at a test for the full condor stack. Because it takes
# an unknown amount of time to complete, it is a good candidate for a regression
# test, but not for unit testing. The DAG stack was tested succesfully running
# the following commands in the cyclopts/tests/files directory:
#
# $ cyclopts condor-submit --rc run_rc.py --db exp_instances.h5 -d test-one-more -k dag -v
# $ cyclopts condor-collect --outdb test-one-more_out.h5 -d test-one-more 
# $ cyclopts combine --files exp_instances.h5 test-one-more_out.h5 -o test-one-more_combined.h5

#
# And this is a previous draft of such a regression test
#

# condor_cmd = """
# cyclopts condor --db {db} --instids {instids} --solvers {solvers} \
#                 --user {user} --localdir {localdir}
# """

# def test_condor():
#     base = os.path.dirname(os.path.abspath(__file__))
#     tstdir = os.path.join(base, 'tmp_{0}'.format(uuid.uuid4()))
#     os.makedirs(tstdir)
#     dbname = 'exp_instances.h5'

#     db = os.path.join(base, 'files', dbname)
#     solvers = "greedy cbc"
#     instids = [x[0] for x in exp_uuid_arcs()[0:2]] # 2 runs
#     user = "gidden"
    
#     timeout = -1 # seconds
#     cmd = condor_cmd.format(db=db, instids=" ".join(instids), 
#                             solvers=solvers, user=user, localdir=tstdir) 
#     print("executing {0}".format(cmd))
#     rtncode, out, err = tools.run(cmd.split(), timeout=timeout, shell=(os.name == 'nt'))
#     if rtncode == -9:
#         print("Process timed out.")
#     if rtncode != 0:
#         print("Error in execution.")
#         print("Stdout: {0}".format(out))
#         print("Stderr: {0}".format(err))
#     assert_equal(0, rtncode)
    
#     h5file = t.open_file(os.path.join(tstdir, dbname), 'r')
#     h5node = h5file.root.Instances.ExchangeInstSolutions
#     assert_equal(h5node.nrows, len(instids) * len(solvers.split()))
#     h5file.close()
    
#     shutil.rmtree(tstdir)
