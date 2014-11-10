"""This module defines methods to lauch Worker Queue Cyclopts jobs.

:author: Matthew Gidden <matthew.gidden _at_ gmail.com>
"""
from __future__ import print_function

import paramiko as pm
import os
import io
import tarfile 
import shutil 
import stat

from cyclopts import tools
from cyclopts.condor.utils import exec_remote_cmd, batlab_base_dir_template

run_lines = u"""#!/bin/bash
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
tar -xf cde-cyclopts-exec.tar.gz
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
../cyclopts.cde exec --db $indb --outdb $outdb --instids $instids \
--solvers {solvers} --family_module {module} --family_class {cname}
echo "execute dir post-execute"
ls -l

mv $outdb $pwd
cd $pwd
echo "pwd dir post-execute"
ls -l
"""

def gen_tar(remotedir, db, instids, module, cname, solvers, 
            user="gidden", verbose=False):
    prepdir = '.tmp_{0}'.format(remotedir)
    if not os.path.exists(prepdir):
        os.makedirs(prepdir)
    else:
        raise IOError("File preparation directory {0} already exists".format(
                prepdir))
    remotehome = batlab_base_dir_template.format(user=user)
    
    nfiles = 0
    runlines = run_lines.format(solvers=" ".join(solvers), module=module, 
                                cname=cname)
    runfile = os.path.join(prepdir, 'run.sh')
    with io.open(runfile, mode='w') as f:
        f.write(runlines)
    # chmod 775
    os.chmod(runfile, stat.S_IRWXG | stat.S_IRWXU | stat.S_IXOTH | stat.S_IROTH)
    nfiles += 1
    idfile = os.path.join(prepdir, 'uuids')
    with io.open(idfile, mode='w') as f:
        for i in instids:
            f.write(u'{0}\n'.format(i))
    nfiles += 1
    base = os.path.dirname(os.path.abspath(__file__))
    mastername = 'launch_master.py'
    masterfile = os.path.join(base, mastername)
    nfiles += 1
    nfiles += 1 # add db
    if verbose:
        print("tarring {0} files".format(nfiles))
    tarname = "{0}.tar.gz".format(remotedir)
    with tarfile.open(tarname, 'w:gz') as tar:
        tar.add(db, arcname="{0}/{1}".format(remotedir, os.path.basename(db)))
        tar.add(runfile, arcname="{0}/{1}".format(remotedir, 
                                                  os.path.basename(runfile)))
        tar.add(idfile, arcname="{0}/{1}".format(remotedir, 
                                                  os.path.basename(idfile)))
        tar.add(masterfile, arcname="{0}/{1}".format(remotedir, 
                                                     os.path.basename(masterfile)))
    shutil.rmtree(prepdir)
    return tarname

submit_cmd = """
mkdir -p {remotedir} && cd {remotedir} &&
tar -xf {tarfile} && rm {tarfile} && cd {cddir} && 
nohup python -u launch_master.py port={port} user={user} nids={nids} indb={indb} nodes={nodes} --log={log} > launch_master.out 2>&1 &
"""

def _submit(client, remotedir, tarname, nids, indb, log=False,
            port='5422', user='gidden', nodes=None, verbose=False):
    """Performs a condor Work Queue sumbission on a client using a tarball of all
    submission-related data.

    Parameters
    ----------
    client : paramiko SSHClient
        the client
    remotedir : str
        the run directory on the client
    tarname : str
        the name of the tarfile
    nids : int
        the number of ids being run
    indb : str
        the name of the input database
    log : bool
        whether or not to keep worker/queue logs
    port : str, optional
        the port for the workers and master to communicate on
    user : str, optional
        the user to run the jobs on
    nodes : list, optional
        a list of execute nodes prefixes (e.g., e121.chtc.wisc.edu -> e121)
    verbose : bool, optional
        whether to print information regarding the submission process    
    """
    ffrom = tarname
    tarname = os.path.basename(tarname)
    fto = '{0}/{1}'.format(remotedir, tarname)
    nodes = ['e121', 'e122', 'e123', 'e124', 'e125', 'e126'] if nodes is None else nodes
    if verbose:
        print("Copying from {0} to {1} on the condor submit node.".format(
                ffrom, fto))
    try:
        ftp = client.open_sftp()
        ftp.put(ffrom, fto)
        ftp.close()
    except IOError as e:
        raise IOError(
            ('Error transferring files to {0}: {1}.').format(remotedir, 
                                                             e.message))
    
    cddir = tarname.split(".tar.gz")[0]
    

    cmd = submit_cmd.format(tarfile=tarname, cddir=cddir, 
                            remotedir=remotedir, port=port, user=user, 
                            nids=nids, indb=indb, log=log, 
                            nodes=",".join(nodes))    
    print("Remotely executing '{0}'".format(cmd))
    stdin, stdout, stderr = client.exec_command(cmd)
    return stdout.channel.recv_exit_status()

def submit(user, db, instids, module, cname, solvers, remotedir, log=False,
           host="submit-3.chtc.wisc.edu", keyfile=None, 
           nodes=None,
           port='5422', verbose=False):
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
    module : str
        the ProblemFamily module
    cname : str
        the ProblemFamily cname
    solvers : list
        the solvers to use
    remotedir : str
        the base run directory on the condor submit node, relative to 
        ~/cyclopts-runs
    log : bool
        whether or not to keep worker/queue logs
    host : str, optional
        the condor submit host
    keyfile : str, optional
        the public key file
    nodes : list, optional
        a list of execute nodes prefixes (e.g., e121.chtc.wisc.edu -> e121)
    port : str, optional
        the port to use for master/worker communication    
    verbose : bool, optional
        whether to print information regarding the submission process    
    """
    client = pm.SSHClient()
    client.set_missing_host_key_policy(pm.AutoAddPolicy())
    _, keyfile, pw = tools.ssh_test_connect(client, host, user, keyfile, auth=True)
    
    localtar = gen_tar(remotedir, db, instids, module, cname, solvers, user, 
                       verbose=verbose)

    if verbose:
        print("connecting to {0}@{1}".format(user, host))
    client.connect(host, username=user, key_filename=keyfile, password=pw)
    
    rtn = _submit(client, tools.cyclopts_remote_run_dir, localtar, 
                  len(instids), os.path.basename(db), log=log, nodes=nodes,
                  port=port, verbose=verbose)
    client.close()
    if verbose:
        print("Submitted job in {0}@{1}:~/cyclopts-runs/{2} with exit "
              "code: {rtn}".format(
                user, host, remotedir, rtn=rtn)) 

    os.remove(localtar)

