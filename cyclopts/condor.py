from __future__ import print_function

import warnings
import tables as t
import shutil
import time
import os
import io

try:
    import paramiko as pm
    import tarfile
    from datetime import datetime
    import getpass
    import glob
except ImportError:
    warnings.warn(("The Condor module was not able to "
                   "import its necessary modules"), ImportWarning)

from cyclopts.tools import combine

batlab_base_dir_template = u"""/home/{user}"""

dag_job_template = u"""JOB J_{0} {0}.sub"""
dag_template = u"""
{job_lines}
DAGMAN_MAX_JOBS_IDLE = 1000
"""

sub_template = u"""
universe = vanilla
executable = run.sh
arguments = {id}.h5 {instids}
output = {id}.out
error = {id}.err
log = {id}.log
requirements = (OpSysAndVer =?= "SL6") && Arch == "X86_64"
should_transfer_files = YES
when_to_transfer_output = ON_EXIT
transfer_input_files = ../../tars/cyclopts-build.tar.gz, {db}
request_cpus = 1
request_memory = 2500
request_disk = 10242880
notification = never
periodic_hold = (JobStatus == 2) && ((CurrentTime - EnteredCurrentStatus) > ({max_time})
queue
"""

run_template = u"""#!/bin/bash
tar -xf cyclopts-build.tar.gz
tar -xf cyclus-install.tar.gz
tar -xf cyclus-deps.tar.gz
tar -xf python-modules.tar.gz
tar -xf python-build.tar.gz
tar -xf scripts.tar.gz
source ./scripts/source.sh
mkdir -p $CYCLOPTS_INST_DIR/lib/python2.7/site-packages/
git clone https://github.com/gidden/cyclopts
cd cyclopts
./setup.py install --user
cd ..;
cyclopts exec --db {db} --solvers {solvers} --outdb $1 --instids $2
rm *.tar.gz
"""

def gen_files(prefix, db, instids, solvers, subfile="dag.sub", max_time=259200):
    """Generates all files needed to run a DAGMan instance of the given input
    database.
    """    
    print("generating files for {0} runs".format(len(instids)))
    if not os.path.exists(prefix):
        os.makedirs(prefix)

    # input db
    shutil.copy(db, prefix)

    # dag submit files
    dag_lines = ""
    for i in range(len(instids)):
        subname = os.path.join(prefix, "{0}.sub".format(i))
        with io.open(subname, 'w') as f:
            print(i, instids[i], os.path.basename(db), max_time)
            f.write(sub_template.format(
                    id=i, instids=instids[i], db=os.path.basename(db),
                    max_time=max_time))
        dag_lines += dag_job_template.format(i) + '\n'
    dagfile = os.path.join(prefix, subfile)
    with io.open(dagfile, 'w') as f:
        f.write(dag_template.format(job_lines=dag_lines))

    # run script
    runfile = os.path.join(prefix, "run.sh")
    with io.open(runfile, 'w') as f:
        f.write(run_template.format(db=os.path.basename(db), 
                                    solvers=" ".join(solvers)))

def wait_till_found(client, path, t_sleep=5):
    """Queries a client if a an expected file exists until it does."""
    print('Waiting for existence of {0}'.format(path))
    found = False
    while not found:
        cmd = "find {0}".format(path)
        print("Remotely executing '{0}'".format(cmd))
        stdin, stdout, stderr = client.exec_command(cmd)
        found = len(stdout.readlines()) > 0
        time.sleep(t_sleep)

def submit(client, remotedir, localdir, tarname, subfile="dag.sub"):
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
    ffrom = os.path.join(localdir, tarname)
    fto = os.path.join(remotedir, tarname)
    print("Copying from {0} to {1} on the condor submit node.".format(
            ffrom, fto))
    try:
        ftp = client.open_sftp()
        ftp.put(ffrom, fto)
        ftp.close()
    except IOError:
        raise IOError(
            'Could not find {0} on the submit node.'.format(remotedir))

    dirname = tarname.split(".tar.gz")[0]
    cmd = ("cd {remotedir} && "
           "tar -xf {0} && "
           "cd {1} && "
           "condor_submit_dag {submit};")
    cmd = cmd.format(tarname, dirname, submit=subfile, remotedir=remotedir)
    print("Remotely executing '{0}'".format(cmd))
    stdin, stdout, stderr = client.exec_command(cmd)
    print("Result:\nstdout: {0}\nstderr: {1}".format(stdout.readlines(), stderr.readlines()))
    
    checkfile = "{remotedir}/{0}/{1}.dagman.out".format(
        dirname, subfile, remotedir=remotedir)
    wait_till_found(client, checkfile)

    cmd = "head {0}".format(checkfile)
    print("Remotely executing '{0}'".format(cmd))
    stdin, stdout, stderr = client.exec_command(cmd)
    err = stderr.readlines()
    if len(err) > 0:
        raise IOError(" ".join(err))
    pid = stdout.readlines()[1].split('condor_scheduniv_exec.')[1].split()[0]

    return pid

def check_finish(client, pid):
    """Checks the status of a condor run on the client.
    """
    cmd = "condor_q {0}".format(pid)
    print("Remotely executing '{0}'".format(cmd))
    stdin, stdout, stderr = client.exec_command(cmd)
    outlines = stdout.readlines()
    idcheck = outlines[-1].split()[0].strip()
    done = False if len(outlines) == 0 else idcheck == 'ID'
    if not done:
        print('Not done yet!')
    return done

def aggregate(client, remotedir, localdir, outdb):
    """After a DAG run has completed, brings all resulting output back to the
    local machine and aggregates them into a single file.

    Parameters
    ----------
    client : paramiko SSHClient
        the client
    remotedir : str
        the landing directory on the client machine
    localdir : str
        the landing directory on the local macine
    outdb : str
        the name of the aggregated output file
    """
    outdir = 'outfiles'
    outtar = '{0}.tar.gz'.format(outdir)
    cmd = ("cd {0}; "
           "mkdir {1}; "
           "mv *_out.h5 {1}; " 
           "tar -czf {2} {1};").format(remotedir, outdir, outtar)
    print("Remotely executing '{0}'".format(cmd))
    stdin, stdout, stderr = client.exec_command(cmd)

    remotetar = '{0}/{1}'.format(remotedir, outtar)
    localtar = '{0}/{1}'.format(localdir, outtar)
    wait_till_found(client, remotetar)
    ftp = client.open_sftp()
    print("Copying {0} from condor submit node to {1}.".format(
            remotetar, localtar))
    ftp.get(remotetar, localtar)
    ftp.close()

    with tarfile.open('{0}/{1}'.format(localdir, outtar), 'r:gz') as f:
        f.extractall(localdir)
    os.remove('{0}/{1}'.format(localdir, outtar))

    files = glob.glob('{0}/{1}/*_out.h5'.format(localdir, outdir))
    combine(files, '{0}/{1}'.format(localdir, outdb))

    shutil.rmtree('{0}/{1}'.format(localdir, outdir))    

def cleanup(client, remotedir):
    """Removes all files in the remote directory."""
    cmd = "rm -rf {0}".format(remotedir)
    print("Remotely executing '{0}'".format(cmd))
    stdin, stdout, stderr = client.exec_command(cmd)
    
def submit_dag(user, db, instids, solvers, outdb=None, 
               host="submit-1.chtc.wisc.edu", localdir=".", 
               remotedir="cyclopts-runs", clean=False, auth=True):
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
    auth : bool, optional
        if true, query password authentication
    """    
    prompt = "Password for {0}@{1}:".format(user, host)
    pw = getpass.getpass(prompt) if auth else None
    ssh = pm.SSHClient()
    ssh.set_missing_host_key_policy(pm.AutoAddPolicy())

    batlab_dir = "{0}/{remotedir}".format(
        batlab_base_dir_template.format(user=user), remotedir=remotedir)
    timestamp = "_".join([str(t) for t in datetime.now().timetuple()][:-3])
    run_dir = os.path.join(localdir, "run_{0}".format(timestamp))

    #
    # begin dagman specific
    #
    max_time = 60 * 60 * 5 # 5 hours
    gen_files(run_dir, db, instids, solvers, 
              max_time=max_time)
    tarname = "{0}.tar.gz".format(os.path.basename(run_dir))
    cwd = os.getcwd()
    os.chdir(localdir)
    with tarfile.open(tarname, 'w:gz') as f:
        f.add(os.path.basename(run_dir))
    os.chdir(cwd)
    shutil.rmtree(run_dir)
    
    print("connecting to {0}@{1}".format(user, host))
    ssh.connect(host, username=user, password=pw)
    pid = submit(ssh, batlab_dir, localdir, tarname)
    ssh.close()
    #
    # end dagman specific
    #

    done = False
    while not done:
        print("Querying status of {0}".format(run_dir))
        print("connecting to {0}@{1}".format(user, host))
        ssh.connect(host, username=user, password=pw)
        done = check_finish(ssh, pid)
        ssh.close()
        if not done:
            time.sleep(300)

    print("{0} has completed.".format(run_dir))

    # create dump directory with aggregate input
    final_in_path = os.path.join(dumpdir, db)
    if not os.path.exists(dumpdir):
        os.mkdir(dumpdir)
    if not os.path.exists(final_in_path):
        shutil.copy(db, dumpdir)
    elif not shutil._samefile(db, final_in_path):
        warnings.warn("Carefull! Overwriting file at {0} with {1}".format(
                final_in_path, db), RuntimeWarning)
        shutil.copy(db, dumpdir)
    
    # aggregate and dump output
    ssh.connect(host, username=user, password=pw)
    print("connecting to {0}@{1}".format(user, host))
    aggregate(ssh, batlab_dir, dumpdir, outdb)
    if clean:
        cleanup(ssh, batlab_dir)
    ssh.close()
