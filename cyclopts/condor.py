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

sub_template = u"""
universe = vanilla
executable = run.sh
arguments = {instids} {id}
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
cyclopts exec --db {db} --solvers {solvers} --instids $1 --outdb $2
rm *.tar.gz
"""

dag_template = u"""JOB J_{0} {0}.sub\n"""

def gen_files(prefix, db, instids, solvers, subfile):
    """Generates all files needed to run a DAGMan instance of the given input
    database.
    """    
    print("generating files for {0} runs".format(nrows))
    dag_lines = ""
    for i in range(instids):
        subname = os.path.join(prefix, "{0}.sub".format(i))
        max_time = 60 * 60 * 5 # 5 hours
        with io.open(subname, 'w') as f:
            f.write(sub_template.format(id=i, instid=instids[i], db=db, 
                                        max_time=max_time))
        dag_lines += dag_template.format(i)
    dag_lines += "DAGMAN_MAX_JOBS_IDLE = 1000\n"

    runfile = os.path.join(prefix, "run.sh")
    solvers = " ".join(solvers)
    with io.open(runfile, 'w') as f:
        f.write(run_template.format(db, solvers=solvers))

    dagfile = os.path.join(prefix, subfile)
    with io.open(dagfile, 'w') as f:
        f.write(dag_lines)

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

def submit(client, rundir, tarname, subfile):
    """Performs a condor DAG sumbission on a client using a tarball of all
    submission-related data.

    Parameters
    ----------
    client : paramiko SSHClient
        the client
    rundir : str
        the run directory on the client
    tarname : str
        data tarball name
    subfile : str
        the name of the submit file
    """
    ftp = client.open_sftp()
    print("Copying {0} to condor submit node.".format(tarname))
    ftp.put(tarname, "{0}/{1}".format(rundir, tarname))
    ftp.close()

    dirname = tarname.split(".tar.gz")[0]
    cmd = ("cd {rundir}; "
           "tar -xf {0}; "
           "cd {1}; "
           "condor_submit_dag {submit};")
    cmd = cmd.format(tarname, dirname, submit=subfile, rundir=rundir)
    print("Remotely executing '{0}'".format(cmd))
    stdin, stdout, stderr = client.exec_command(cmd)
    
    checkfile = "{rundir}/{0}/{1}.dagman.out".format(
        dirname, subfile, rundir=rundir)
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
    done = False if len(outlines) == 0 else outlines[-1].split()[0] == 'ID'
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
    
def submit_dag(user, host, indb, instids, solvers, dumpdir, outdb, clean, auth):
    """Connects via SSH to a condor submit node, and executes a Cyclopts DAG
    run.
    
    Parameters
    ----------
    user : str
        the user on the condor submit host
    host : str
        the condor submit node host (e.g. submit-1.chtc.wisc.edu)
    indb : str
        the input database location
    instids : set
        the set of instances to run
    solvers : list
        the solvers to use
    dumpdir : str
        the final run directory (where the input and output database files 
        will be located)
    outdb : str
        the output database location
    clean : bool
        if true, removes the working directory on the submit node
    auth : bool
        if true, query a password authentication
    """
    timestamp = "_".join([str(t) for t in datetime.now().timetuple()][:-3])
    
    prompt = "Password for {0}@{1}:".format(user, host)
    pw = getpass.getpass(prompt) if auth else None
    ssh = pm.SSHClient()
    ssh.set_missing_host_key_policy(pm.AutoAddPolicy())

    run_dir = "run_{0}".format(timestamp)
    sub_dir = "/home/{0}/cyclopts-runs".format(user)
    remote_dir = "{0}/{1}".format(sub_dir, run_dir)

    if not os.path.exists(run_dir):
        os.mkdir(run_dir)
    shutil.copy(indb, run_dir)

    #
    # begin dagman specific
    #
    subfile = "dag.sub"
    gen_files(run_dir, indb, instids, solvers, subfile)
    tarname = "{0}.tar.gz".format(run_dir)
    with tarfile.open(tarname, 'w:gz') as f:
        f.add(run_dir)
    shutil.rmtree(run_dir)
    
    print("connecting to {0}@{1}".format(user, host))
    ssh.connect(host, username=user, password=pw)
    pid = submit(ssh, sub_dir, tarname, subfile)
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
        time.sleep(300)

    print("{0} has completed.".format(run_dir))

    # create dump directory with aggregate input
    final_in_path = os.path.join(dumpdir, indb)
    if not os.path.exists(dumpdir):
        os.mkdir(dumpdir)
    if not os.path.exists(final_in_path):
        shutil.copy(indb, dumpdir)
    elif not shutil._samefile(indb, final_in_path):
        warnings.warn("Carefull! Overwriting file at {0} with {1}".format(
                final_in_path, indb), RuntimeWarning)
        shutil.copy(indb, dumpdir)
    
    # aggregate and dump output
    ssh.connect(host, username=user, password=pw)
    print("connecting to {0}@{1}".format(user, host))
    aggregate(ssh, remote_dir, dumpdir, outdb)
    if clean:
        cleanup(ssh, remote_dir)
    ssh.close()
