from cyclopts import main
from cyclopts import tools
from cyclopts import condor

from cyclopts.structured_species.request import StructuredRequest

import os
import shutil
import tables as t
import uuid
import subprocess
import numpy as np
from numpy.testing import assert_array_equal
import paramiko as pm
import warnings
from collections import defaultdict

import nose
from nose.tools import assert_equal, assert_true, assert_almost_equal, \
    assert_less_equal

from utils import timeout, TimeoutError

def test_exec():
    infile = 'obs_valid_in.h5'
    ninst = 4
    
    base = os.path.dirname(os.path.abspath(__file__))
    db = os.path.join(base, "tmp_{0}.h5".format(str(uuid.uuid4())))
    shutil.copy(os.path.join(base, 'files', infile), db)
    solvers = "greedy, clp, cbc" # greedy is different for one, unsure why
    cmd = ("cyclopts exec --db={0} --family_class ResourceExchange "
           "--family_module cyclopts.exchange_family "
           "--solvers {1}").format(db, solvers)
    assert_equal(0, subprocess.call(cmd.split(), shell=(os.name == 'nt')))
    
    h5file = t.open_file(db, 'r')
    path = '/Results'
    h5node = h5file.get_node(path)
    assert_equal(h5node.nrows, ninst * len(solvers.split()))
    objs = defaultdict(dict)
    for row in h5node.iterrows():
        objs[row['instid']][row['solver']] = row['objective']
    h5file.close()
    
    # check that all solvers get the same answer
    for iid, solvers in objs.items():
        assert_almost_equal(solvers['cbc'], solvers['greedy'])
        assert_less_equal(solvers['clp'], solvers['cbc'])
            
    if os.path.exists(db):
        os.remove(db)

def test_convert():
    base = os.path.dirname(os.path.abspath(__file__))
    rc = os.path.join(base, 'files', 'obs_valid.rc')    
    db = os.path.join(base, "tmp_{0}.h5".format(str(uuid.uuid4())))

    ninst = 2
    nvalid = 4

    cmd = "cyclopts convert --rc {0} --db {1} -n {2}".format(rc, db, ninst)
    assert_equal(0, subprocess.call(cmd.split(), shell=(os.name == 'nt')))
    h5file = t.open_file(db, 'r')
    
    sp = StructuredRequest()
    path = '/'.join(['', 'Species', sp.name])
    h5node = h5file.get_node(path, sp.sum_tbl_name)
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
# $ cyclopts condor-submit --rc run_rc.py --db obs_valid_in.h5 -d test-one-more -k dag -v
# $ cyclopts condor-collect --outdb test-one-more_out.h5 -d test-one-more 
# $ cyclopts combine --files obs_valid_in.h5 test-one-more_out.h5 -o test-one-more_combined.h5

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
#     dbname = 'obs_valid_in.h5'

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
