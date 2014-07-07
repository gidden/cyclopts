from __future__ import print_function

import paramiko as pm

from cyclopts import tools
from cyclopts.condor.utils import _wait_till_found, batlab_base_dir_template

run_lines = """#!/bin/bash
pwd=$PWD
outdb=$1
instids=$2
# work queue puts workers down two directories
indb_rel=../../$3
indb_abs=`readlink -f $indb_rel`
indb_dir=`dirname $indb_abs`
indb=`basename $indb_abs`

echo "pwd: $PWD"
echo "indb_rel : $indb_rel"
echo "indb dir: $indb_dir"
echo "indb dir listing"
ls -l $indb_dir

echo "indb_abs: $indb_abs"
if [ ! -f $indb_abs ]; then
    echo "expected input file $indb_abs does not exist"
    exit 1
fi

echo "pwd pre-tar:"
ls -l
tar -xf CDE.tar.gz
tar -xf cde-cyclopts.tar.gz
export PATH=$pwd/CDE/:$PATH
echo "pwd post-tar:"
ls -l

cde_root='cde-package/cde-root'
ln $indb_abs $cde_root/$indb
cd $cde_root
sed -i 's/..\/cde-exec/cde-exec/g' ../cyclopts.cde

echo "confirming $indb exists:"
if [ ! -f $indb ]; then
    echo "expected input file $indb does not exist"
    exit 1
fi

echo "execute dir pre-execute"
ls -l

echo "Executing ../cyclopts.cde exec --db $indb --outdb $outdb --instids $instids"
../cyclopts.cde exec --db $indb --outdb $outdb --instids $instids
echo "execute dir post-execute"
ls -l

mv $outdb $pwd
cd $pwd
echo "pwd dir post-execute"
ls -l
"""

def gen_tar(remotedir, db, instids, solvers, user, verbose=False):
    prepdir = '.tmp_{0}'.format(remotedir)
    if not os.path.exists(prepdir):
        os.makedirs(prepdir)
    else:
        raise IOError("File preparation directory {0} already exists".format(
                prepdir))
    remotehome = batlab_base_dir_template.format(user=user)

    nfiles += 1 # add db
    if verbose:
        print("tarring {0} files".format(nfiles))
    tarname = "{0}.tar.gz".format(remotedir)
    with tarfile.open(tarname, 'w:gz') as tar:
        tar.add(db, arcname="{0}/{1}".format(remotedir, os.path.basename(db)))
        
    shutil.rmtree(prepdir)
    return tarname


def submit_work_queue(user, db, instids, solvers, remotedir, 
                      host="submit-3.chtc.wisc.edu", keyfile=None, 
                      verbose=False):
    """Connects via SSH to a condor submit node, and executes a Cyclopts Work
    Queue run.
    
    Parameters
    ----------
    user : str
        the user on the condor submit host
    db : str
        the problem instance database
    instids : set
        the set of instances to run
    solvers : list
        the solvers to use
    remotedir : str
        the base run directory on the condor submit node, relative to 
        ~/cyclopts-runs
    host : str, optional
        the condor submit host
    keyfile : str, optional
        the public key file    
    verbose : bool, optional
        whether to print information regarding the submission process    
    """
    client = pm.SSHClient()
    client.set_missing_host_key_policy(pm.AutoAddPolicy())
    _, keyfile = tools.ssh_test_connect(client, host, user, keyfile, auth=True)
    
    
    localtar = gen_tar(remotedir, db, instids, solvers, user, 
                       verbose=verbose)

    if verbose:
        print("connecting to {0}@{1}".format(user, host))
    client.connect(host, username=user, key_filename=keyfile)
    
    pid = _submit(client, tools.cyclopts_remote_run_dir, localtar, 
                      verbose=verbose)
    client.close()
    if verbose:
        print("Submitted job in {0}@{1}:~/{2} with pid: {3}".format(
                user, host, remotedir, pid)) 

    os.remove(localtar)

