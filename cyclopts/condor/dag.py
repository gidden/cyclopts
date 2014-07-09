from __future__ import print_function

import os
import io
import paramiko as pm
import glob
import tarfile
import shutil
import uuid

from cyclopts import tools
from cyclopts.condor.utils import _wait_till_found, batlab_base_dir_template

job_template = u"""JOB J_{0} {0}.sub"""

# This submission file template includes a condor execute node requirement
# called ForGidden. This requirement is used to target nonhyperthreaded cores in
# order to get accurate time comparisons for problem instance runs. In the
# future, if this tool is used by others, ForGidden should be changed on the
# Condor side to ForCyclopts, ForTimeMeasurement, or an equivalent, and this
# template should be updated. Contact chtc@cs.wisc.edu to do so.
sub_template = u"""
universe = vanilla
executable = run.sh
arguments = "'{id}_out.h5' '{instids}'"
output = {id}.out
error = {id}.err
log = {id}.log
requirements = (OpSysAndVer =?= "SL6") && Arch == "X86_64" && ( ForGidden == true )
should_transfer_files = YES
when_to_transfer_output = ON_EXIT
transfer_input_files = {homedir}/cde-cyclopts.tar.gz, {homedir}/CDE.tar.gz, {db}
request_cpus = 1
#request_memory = 2500
#request_disk = 10242880
notification = never
"""

run_template = u"""#!/bin/bash
pwd=$PWD
ls -l

tar -xf CDE.tar.gz
tar -xf cde-cyclopts.tar.gz
export PATH=$pwd/CDE/:$PATH
ls -l

mv exp_instances.h5 cde-package/cde-root
cd cde-package/cde-root
sed -i 's/..\/cde-exec/cde-exec/g' ../cyclopts.cde
ls -l
../cyclopts.cde exec --db {db} --solvers {solvers} --outdb $1 --instids $2
mv $1 $pwd

cd $pwd
ls -l
"""

submit_cmd = """
mkdir -p {remotedir} && cd {remotedir} &&
tar -xf {tarfile} && cd {cddir} && 
condor_submit -maxidle 1000 {submit};
"""

def _gen_files(prepdir, dbname, instids, solvers, remotehome, subfile="dag.sub", 
                   max_time=None, verbose=False):
    """Generates all files needed to run a DAGMan instance of the given input
    database.
    """    
    if verbose:
        print("generating files for {0} runs".format(len(instids)))

    # dag submit files
    max_time_line = ("\nperiodic_hold = (JobStatus == 2) && "
                     "((CurrentTime - EnteredCurrentStatus) > "
                     "({0}))").format(max_time) if max_time is not None \
                     else ""
    lines = ""
    nfiles = len(instids)
    for i in range(len(instids)):
        subname = os.path.join(prepdir, "{0}.sub".format(i))
        with io.open(subname, 'w') as f:
            sublines = sub_template.format(id=i, instids=instids[i], db=dbname,
                                           homedir=remotehome)
            sublines += max_time_line + '\nqueue'
            f.write(sublines)
        lines += job_template.format(i) + '\n'
    dagfile = os.path.join(prepdir, subfile)
    nfiles += 1
    with io.open(dagfile, 'w') as f:
        f.write(lines)
        
    # run script
    runfile = os.path.join(prepdir, "run.sh")
    nfiles += 1 
    with io.open(runfile, 'w') as f:
        f.write(run_template.format(db=dbname, solvers=" ".join(solvers)))
    
    return nfiles

def _submit(client, remotedir, tarname, subfile="dag.sub", 
                verbose=False):
    """Performs a condor DAG sumbission on a client using a tarball of all
    submission-related data.

    Parameters
    ----------
    client : paramiko SSHClient
        the client
    remotedir : str
        the run directory on the client
    tarname : str
        the name of the tarfile
    subfile : str, optional
        the name of the submit file
    verbose : bool, optional
        whether to print information regarding the submission process    
    """
    ffrom = tarname
    tarname = os.path.basename(tarname)
    fto = '{0}/{1}'.format(remotedir, tarname)
    if verbose:
        print("Copying from {0} to {1} on the condor submit node.".format(
                ffrom, fto))
    try:
        ftp = client.open_sftp()
        ftp.put(ffrom, fto)
        ftp.close()
    except IOError:
        raise IOError(
            'Could not find {0} on the submit node.'.format(remotedir))
    
    cddir = tarname.split(".tar.gz")[0]
    cmd = submit_cmd.format(tarfile=tarname, cddir=cddir, 
                            submit=subfile, remotedir=remotedir)
    print("Remotely executing '{0}'".format(cmd))
    stdin, stdout, stderr = client.exec_command(cmd)
    
    checkfile = "{remotedir}/{0}/{1}.dagman.out".format(
        cddir, subfile, remotedir=remotedir)
    _wait_till_found(client, checkfile)

    cmd = "head {0}".format(checkfile)
    if verbose:
        print("Remotely executing '{0}'".format(cmd))
    stdin, stdout, stderr = client.exec_command(cmd)
    err = stderr.readlines()
    if len(err) > 0:
        raise IOError(" ".join(err))
    pid = stdout.readlines()[1].split('condor_scheduniv_exec.')[1].split()[0]

    return pid

def gen_tar(rundir, db, instids, solvers, user="gidden", verbose=False):
    prepdir = '.tmp_{0}'.format(rundir)
    if not os.path.exists(prepdir):
        os.makedirs(prepdir)
    else:
        raise IOError("File preparation directory {0} already exists".format(
                prepdir))
    print(prepdir)
    max_time = 60 * 60 * 5 # 5 hours
    remotehome = batlab_base_dir_template.format(user=user)
    nfiles = _gen_files(prepdir, os.path.basename(db), instids, solvers, 
                            remotehome, max_time=max_time, verbose=verbose)
    
    subfiles = glob.iglob(os.path.join(prepdir, '*.sub'))
    shfiles = glob.iglob(os.path.join(prepdir, '*.sh'))

    nfiles += 1 # add db
    if verbose:
        print("tarring {0} files".format(nfiles))
    tarname = "{0}.tar.gz".format(rundir)
    with tarfile.open(tarname, 'w:gz') as tar:
        tar.add(db, arcname="{0}/{1}".format(rundir, os.path.basename(db)))
        for f in subfiles:
            basename = os.path.basename(f)
            tar.add(f, arcname="{0}/{1}".format(rundir, basename))
        for f in shfiles:
            basename = os.path.basename(f)
            tar.add(f, arcname="{0}/{1}".format(rundir, basename))
    shutil.rmtree(prepdir)
    return tarname

def submit(user, db, instids, solvers, remotedir, 
               host="submit-3.chtc.wisc.edu", keyfile=None, verbose=False):
    """Connects via SSH to a condor submit node, and executes a Cyclopts DAG
    run.
    
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
    _, keyfile, pw = tools.ssh_test_connect(client, host, user, keyfile, auth=True)

    localtar = gen_tar(remotedir, db, instids, solvers, user, 
                       verbose=verbose)

    if verbose:
        print("connecting to {0}@{1}".format(user, host))
    client.connect(host, username=user, key_filename=keyfile, password=pw)
    
    pid = _submit(client, tools.cyclopts_remote_run_dir, localtar, 
                      verbose=verbose)
    client.close()
    if verbose:
        print("Submitted job in {0}@{1}:~/cyclopts-runs/{2} with pid: {3}".format(
                user, host, remotedir, pid)) 

    os.remove(localtar)
