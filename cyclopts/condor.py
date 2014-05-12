from __future__ import print_function

import paramiko as pm
import tables as t
import tarfile
import shutil
from datetime import datetime
import getpass
import time
import os
import io

rc_template = u"""
path = {0} 
rows = range({1}, {2})
"""

sub_template = u"""
universe = vanilla
executable = run.sh
arguments = {0}
output = {0}.out
error = {0}.err
log = {0}.log
requirements = (OpSysAndVer =?= "SL6") && Arch == "X86_64"
should_transfer_files = YES
when_to_transfer_output = ON_EXIT
transfer_input_files = ../../cyclopts-build.tar.gz, {1}, {0}.rc
request_cpus = 1
request_memory = 2500
request_disk = 10242880
notification = never
queue
"""

run_template = u"""
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
cyclopts exec -i {0} -o $1_out.h5 --rc=$1.rc
rm *.tar.gz
"""

dag_template = u"""JOB J_{0} {0}.sub\n"""

def gen_files(prefix=".", db="in.h5", tbl="ReactorRequestSampler", subfile = "dag.sub"):
    """Generates all files needed to run a DAGMan instance of the given input
    database.
    """
    h5file = t.open_file(db, mode='r')
    if hasattr(h5file.root, tbl):
        tbl = getattr(h5file.root, tbl)
    else:
        raise IOError("Can't find table with name {0}.".format(tbl))
    nrows = tbl.nrows
    h5file.close()
    
    print("generating files for {0} runs".format(nrows))
    dag_lines = ""
    for i in range(nrows):
        rcname = os.path.join(prefix, "{0}.rc".format(i))
        with io.open(rcname, 'w') as f:
            f.write(rc_template.format(tbl, i, i+1))
        subname = os.path.join(prefix, "{0}.sub".format(i))
        with io.open(subname, 'w') as f:
            f.write(sub_template.format(i, db))
        dag_lines += dag_template.format(i)
    
    runfile = os.path.join(prefix, "run.sh")
    with io.open(runfile, 'w') as f:
        f.write(run_template.format(db))

    dagfile = os.path.join(prefix, "dag.sub")
    with io.open(dagfile, 'w') as f:
        f.write(dag_lines)

def submit(user, host, pw, tarname, subfile):
    user = user
    host = host
    pw = pw
    ssh = pm.SSHClient()
    ssh.set_missing_host_key_policy(pm.AutoAddPolicy())
    print("connecting to {0}@{1}".format(user, host))
    ssh.connect(host, username=user, password=pw)

    ftp = ssh.open_sftp()
    print("Copying {0} to condor submit node.".format(tarname))
    ftp.put(tarname, "/home/{0}/cyclopts-runs/{1}".format(user, tarname))
    ftp.close()

    dirname = tarname.split(".tar.gz")[0]
    cmd = ("cd /home/{user}/cyclopts-runs; "
           "tar -xf {0}; "
           "cd {1}; "
           "condor_submit_dag {submit};")
    cmd = cmd.format(tarname, dirname, submit=subfile, user=user)
    print("Remotely executing '{0}'".format(cmd))
    stdin, stdout, stderr = ssh.exec_command(cmd)
    
    checkfile = "{0}.dagman.out".format(subfile)
    found = False
    while not found:
        cmd = "find /home/{user}/cyclopts-runs/{0}/{1}".format(dirname, checkfile, user=user)
        print("Remotely executing '{0}'".format(cmd))
        stdin, stdout, stderr = ssh.exec_command(cmd)
        found = len(stdout.readlines()) > 0
        time.sleep(5)

    cmd = "head /home/{user}/cyclopts-runs/{0}/{1}".format(dirname, checkfile, user=user)
    print("Remotely executing '{0}'".format(cmd))
    stdin, stdout, stderr = ssh.exec_command(cmd)
    err = stderr.readlines()
    if len(err) > 0:
        raise IOError(" ".join(err))
    pid = stdout.readlines()[1].split('condor_scheduniv_exec.')[1].split()[0]

    ssh.close()
    return pid

def check_finish(user, host, pw, pid):
    user = user
    host = host
    pw = pw
    ssh = pm.SSHClient()
    ssh.set_missing_host_key_policy(pm.AutoAddPolicy())
    print("connecting to {0}@{1}".format(user, host))
    ssh.connect(host, username=user, password=pw)

    cmd = "condor_q {0}".format(pid)
    print("Remotely executing '{0}'".format(cmd))
    stdin, stdout, stderr = ssh.exec_command(cmd)
    done = stdout.readlines()[-1].split()[0] == 'ID'

    ssh.close()
    return done

def cleanup(user, host, pw, dirname, dumpdir):
    user = user
    host = host
    pw = pw
    ssh = pm.SSHClient()
    ssh.set_missing_host_key_policy(pm.AutoAddPolicy())
    print("connecting to {0}@{1}".format(user, host))
    ssh.connect(host, username=user, password=pw)

    
    # print("Remotely executing '{0}'".format(cmd))
    # stdin, stdout, stderr = ssh.exec_command(cmd)

    ssh.close()

def submit_dag(user, host, dbname, dumpdir, clean):
    prompt = "Password for {0}@{1}:".format(user, host)
    pw = getpass.getpass(prompt)

    dirname = "run_{0}".format(
        "_".join([str(t) for t in datetime.now().timetuple()][:-3]))

    os.mkdir(dirname)
    shutil.copy(dbname, dirname)
    subfile = "dag.sub"
    gen_files(prefix=dirname, db=dbname, subfile=subfile)
    tarname = "{0}.tar.gz".format(dirname)
    with tarfile.open(tarname, 'w:gz') as f:
        f.add(dirname)
    shutil.rmtree(dirname)
    
    pid = submit(user, host, pw, tarname, subfile)

    done = False
    while not done:
        print("Querying status of {0}".format(dirname))
        done = check_finish(user, host, pw, pid)
        time.sleep(20)

    print("{0} has completed.".format(dirname))

    if clean:
        cleanup(user, host, pw, dirname, dumpdir)
