from __future__ import print_function

import paramiko as pm

from cyclopts import tools
from cyclopts.condor.utils import _wait_till_found

run_lines = """#!/bin/bash             
pwd=$PWD
ls -l
tar -xf CDE.tar.gz
tar -xf cde-cyclopts.tar.gz
export PATH=$pwd/CDE/:$PATH
ls -l
cd cde-package/cde-root
sed -i 's/..\/cde-exec/cde-exec/g' ../cyclopts.cde
ls -l
../cyclopts.cde exec --db $pwd/$3/instances.h5 --outdb $1 --instids $2
mv $1 $pwd
cd $pwd
ls -l
"""

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
    
