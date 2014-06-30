from __future__ import print_function

import warnings
import tables as t
import shutil
import time
import os
import io
import glob 
import uuid

try:
    import paramiko as pm
    import tarfile
    from datetime import datetime
    import getpass
    import glob
except ImportError:
    warnings.warn(("The Condor module was not able to "
                   "import its necessary modules"), ImportWarning)

from cyclopts import tools

batlab_base_dir_template = u"""/home/{user}"""

dag_job_template = u"""JOB J_{0} {0}.sub"""

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
requirements = (OpSysAndVer =?= "SL6") && Arch == "X86_64"
# && ( ForGidden == true )
should_transfer_files = YES
when_to_transfer_output = ON_EXIT
transfer_input_files = {tardir}/cde-cyclopts.tar.gz, {tardir}/CDE.tar.gz, {db}
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
condor_submit_dag -maxidle 1000 {submit};
"""

tar_output_cmd = """
cd {remotedir} && ls -l && tar -czf {tardir}.tar.gz {re}
"""

def gen_files(rundir, dbname, instids, solvers, tardir, subfile="dag.sub", 
              max_time=None, localdir="."):
    """Generates all files needed to run a DAGMan instance of the given input
    database.
    """    
    print("generating files for {0} runs".format(len(instids)))
    files = []

    prepdir = os.path.join(localdir, rundir)
    if not os.path.exists(prepdir):
        os.makedirs(prepdir)

    # dag submit files
    max_time_line = ("\nperiodic_hold = (JobStatus == 2) && "
                     "((CurrentTime - EnteredCurrentStatus) > "
                     "({0}))").format(max_time) if max_time is not None \
                     else ""
    dag_lines = ""
    for i in range(len(instids)):
        subname = os.path.join(prepdir, "{0}.sub".format(i))
        with io.open(subname, 'w') as f:
            sublines = sub_template.format(id=i, instids=instids[i], db=dbname,
                                           tardir=tardir)
            sublines += max_time_line + '\nqueue'
            f.write(sublines)
            files.append(subname)
        dag_lines += dag_job_template.format(i) + '\n'
    dagfile = os.path.join(prepdir, subfile)
    with io.open(dagfile, 'w') as f:
        f.write(dag_lines)
        files.append(dagfile)
        
    # run script
    runfile = os.path.join(prepdir, "run.sh")
    with io.open(runfile, 'w') as f:
        f.write(run_template.format(db=dbname, solvers=" ".join(solvers)))
        files.append(runfile)
    
    return files

def get_files(client, remotedir, localdir, re):
    """Retrieves all files matching an expression on a remote site.

    Parameters
    ----------
    client : paramiko SSHClient
        the client
    remotedir : str
        the output directory on the client machine
    localdir : str
        the output directory on the local macine
    re : str
        the pattern to match
    """
    tardir = 'outfiles'
    cmd = tar_output_cmd.format(remotedir=remotedir, tardir=tardir, re=re)
    print("Remotely executing '{0}'".format(cmd))
    stdin, stdout, stderr = client.exec_command(cmd)

    remotetar = os.path.join(remotedir, '{0}.tar.gz'.format(tardir))
    localtar = os.path.join(localdir, '{0}.tar.gz'.format(tardir))
    _wait_till_found(client, remotetar)
    ftp = client.open_sftp()
    print("Copying {0} from condor submit node to {1}.".format(
            remotetar, localtar))
    ftp.get(remotetar, localtar)
    ftp.close()

    with tarfile.open(localtar, 'r:gz') as f:
        files = f.getnames()
        nfiles = len(files)
        f.extractall(localdir)
    
    print("retrived {0} files from tarball".format(nfiles))

    os.remove(localtar)
    return nfiles
        
def _wait_till_found(client, path, t_sleep=5):
    """Queries a client if a an expected file exists until it does."""
    print('Waiting for existence of {0}'.format(path))
    found = False
    while not found:
        cmd = "find {0}".format(path)
        print("Remotely executing '{0}'".format(cmd))
        stdin, stdout, stderr = client.exec_command(cmd)
        found = len(stdout.readlines()) > 0
        if not found:
            print('Not there yet! Checking again in {0} seconds.'.format(
                    t_sleep))
            time.sleep(t_sleep)

def _wait_till_done(client, user, host, keyfile, pid, t_sleep=300):
    """Queries a client if a an expected process is done."""
    done = False
    while not done:
        print("Querying status of {0}".format(pid))
        print("connecting to {0}@{1}".format(user, host))
        client.connect(host, username=user, key_filename=keyfile)
        done = _check_finish(client, pid)
        client.close()
        if not done:
            print('Not done yet! Checking again in {0} minutes.'.format(
                    t_sleep / 60.))
            time.sleep(t_sleep)

def _check_finish(client, pid):
    """Checks the status of a condor run on the client.
    """
    cmd = "condor_q {0}".format(pid)
    print("Remotely executing '{0}'".format(cmd))
    stdin, stdout, stderr = client.exec_command(cmd)
    outlines = stdout.readlines()
    done = False
    donecheck = 'ID'
    if len(outlines) > 0 and len(outlines[-1].split()) > 0 \
            and outlines[-1].split()[0].strip() == donecheck:
        done = True
    return done

def _submit(client, remotedir, localdir, tarname, subfile="dag.sub"):
    """Performs a condor DAG sumbission on a client using a tarball of all
    submission-related data.

    Parameters
    ----------
    client : paramiko SSHClient
        the client
    remotedir : str
        the run directory on the client
    localdir : str
        the local directory in which the tarfile is located
    tarname : str
        the name of the tarfile
    subfile : str, optional
        the name of the submit file
    """
    tarname = os.path.basename(tarname)
    ffrom = os.path.join(localdir, tarname)
    fto = '{0}/{1}'.format(remotedir, tarname)
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
    print("Remotely executing '{0}'".format(cmd))
    stdin, stdout, stderr = client.exec_command(cmd)
    err = stderr.readlines()
    if len(err) > 0:
        raise IOError(" ".join(err))
    pid = stdout.readlines()[1].split('condor_scheduniv_exec.')[1].split()[0]

    return pid
    
def submit_dag(user, db, instids, solvers, outdb=None, 
               host="submit-3.chtc.wisc.edu", localdir=".", 
               remotedir="cyclopts-runs", clean=False, keyfile=None, cp=True, 
               mv=False, t_sleep=300):
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
    outdb : str, optional
        the output database (i.e., don't write output to db)
    host : str, optional
        the condor submit host
    localdir : str, optional
        the local directory in which results will be placed
    remotedir : str, optional
        the base run directory on the condor submit node
    clean : bool, optional
        if true, removes the working directory on the submit node upon 
        completion, which is automatically created relative to remotedir
    keyfile : str, optional
        the public key file    
    cp : bool, optional
        if true, a copy of the parameter space database is made in the 
        localdir location
    mv : bool, optional
        if true, the parameter space database is moved into the 
        localdir location
    t_sleep : int, optional
        how long to wait (seconds) before checking the progress of a run
    """
    if mv and cp:
        raise ValueError("Can not both move and copy the parameter space "
                         "database.")
    
    if not mv and not cp and outdb is None:
        raise ValueError("Must either move or copy the parameter space "
                         "database if an output database is not provided.")

    client = pm.SSHClient()
    client.set_missing_host_key_policy(pm.AutoAddPolicy())
    _, keyfile = tools.ssh_test_connect(client, host, user, keyfile, auth=True)

    batlab_dir = "{0}/{remotedir}".format(
        batlab_base_dir_template.format(user=user), remotedir=remotedir)
    timestamp = "_".join([str(t) for t in datetime.now().timetuple()][:-3])
    run_dir = "run_{0}".format(timestamp)

    #
    # begin dagman specific
    #
    max_time = 60 * 60 * 5 # 5 hours
    files = gen_files(run_dir, os.path.basename(db), instids, solvers, 
                      batlab_base_dir_template.format(user=user), 
                      max_time=max_time, localdir=localdir)
    files.append(db)
    print("tarring files: {0}".format(", ".join(files)))
    tarname = os.path.join(localdir, "{0}.tar.gz".format(run_dir))
    with tarfile.open(tarname, 'w:gz') as tar:
        for f in files:
            basename = os.path.basename(f)
            tar.add(f, arcname="{0}/{1}".format(run_dir, basename))
    shutil.rmtree(os.path.join(localdir, run_dir))
    
    print("connecting to {0}@{1}".format(user, host))
    client.connect(host, username=user, key_filename=keyfile)
    pid = _submit(client, batlab_dir, localdir, tarname)
    client.close()
    os.remove(tarname)
    #
    # end dagman specific
    #

    _wait_till_done(client, user, host, keyfile, pid, t_sleep=t_sleep)
    print("{0} has completed.".format(run_dir))

    # create aggregation directory, aggregate output, and combine with input if
    # desired
    aggdir = os.path.join(localdir)
    if not os.path.exists(aggdir):
        os.mkdir(aggdir)    

    # copy/move files as soon as job is submitted, and assign it a value if we
    # did so
    if cp:
        shutil.copy(db, aggdir)
    if mv:
        shutil.move(db, aggdir)
    localdb = os.path.join(aggdir, os.path.basename(db))
    localdb = localdb if os.path.exists(localdb) else None

    client.connect(host, username=user, key_filename=keyfile)
    print("connecting to {0}@{1}".format(user, host))

    # get files and clean up
    re = '*_out.h5'
    nfiles = get_files(client, '{0}/{1}'.format(batlab_dir, run_dir), aggdir, 
                       re)
    if clean:
        cleandir = '{0}/{1}'.format(batlab_dir, run_dir)
        cmd = "rm -r {0} && rm {0}.tar.gz".format(cleandir)
        print("Remotely executing '{0}'".format(cmd))
        stdin, stdout, stderr = client.exec_command(cmd)
    client.close()
    
    # combine files and clean up
    files = glob.iglob(os.path.join(aggdir, re))
    new_file = outdb if outdb is not None else \
        os.path.join(aggdir, '{0}_out.h5'.format(run_dir))
    stmt = "Combining {0} databases into {1}".format(
        nfiles, new_file)
    print(stmt)
    tools.combine(files, new_file=new_file)

    if localdb is not None and outdb is None:
        print("Combining input and output dbs, and cleaning up output.")
        tools.combine([localdb, new_file])    
        os.remove(new_file)

def collect(localdir, remotedir, user, host="submit-3.chtc.wisc.edu", 
            outdb='cyclopts_results.h5', clean=False, keyfile=None):
    client = pm.SSHClient()
    client.set_missing_host_key_policy(pm.AutoAddPolicy())
    _, keyfile = tools.ssh_test_connect(client, host, user, keyfile=keyfile, 
                                        auth=False)
    client.connect(host, username=user, key_filename=keyfile)
    print("connecting to {0}@{1}".format(user, host))

    if not os.path.exists(localdir):
        os.makedirs(localdir)    

    # get files and clean up
    nfiles = get_files(client, remotedir, localdir, '*_out.h5')
    
    if clean:
        cmd = "rm -r {0} && rm {0}.tar.gz".format(remotedir)
        print("Remotely executing '{0}'".format(cmd))
        stdin, stdout, stderr = client.exec_command(cmd)
    client.close()
    
    # combine files and clean up
    files = glob.iglob(os.path.join(localdir, '*_out.h5'))
    stmt = "Combining {0} databases into {1}".format(nfiles, outdb)
    print(stmt)
    tools.combine(files, new_file=outdb, clean=True)
