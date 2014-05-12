from __future__ import print_function

try:
    import tables as t
    import paramiko as pm
    import tarfile
    import shutil
    from datetime import datetime
    import getpass
    import time
    import os
    import io
    import glob
except ImportError:
    import warnings
    warnings.warn(("The Condor module was not able to "
                   "import its necessary modules"), ImportWarning)

from cyclopts.tools import combine

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
transfer_input_files = ../../tars/cyclopts-build.tar.gz, {1}, {0}.rc
request_cpus = 1
request_memory = 2500
request_disk = 10242880
notification = never
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
cyclopts exec -i {0} -o $1_out.h5 --solvers={solvers} --rc=$1.rc 
rm *.tar.gz
"""

test_run_template = u"""#!/bin/bash
echo $1
touch $1_out.h5
touch 2_out.h5
touch 3_out.h5
"""

dag_template = u"""JOB J_{0} {0}.sub\n"""

def gen_files(prefix=".", db="in.h5", solvers=['cbc'], tblname="ReactorRequestSampler", subfile = "dag.sub"):
    """Generates all files needed to run a DAGMan instance of the given input
    database.
    """
    h5file = t.open_file(db, mode='r')
    if hasattr(h5file.root, tblname):
        tbl = getattr(h5file.root, tblname)
    else:
        raise IOError("Can't find table with name {0}.".format(tbl))
    nrows = tbl.nrows
    h5file.close()
    
    print("generating files for {0} runs".format(nrows))
    dag_lines = ""
    for i in range(nrows):
        rcname = os.path.join(prefix, "{0}.rc".format(i))
        with io.open(rcname, 'w') as f:
            f.write(rc_template.format(tblname, i, i+1))
        subname = os.path.join(prefix, "{0}.sub".format(i))
        with io.open(subname, 'w') as f:
            f.write(sub_template.format(i, db.split("/")[-1]))
        dag_lines += dag_template.format(i)
    
    runfile = os.path.join(prefix, "run.sh")
    with io.open(runfile, 'w') as f:
        f.write(run_template.format(db))
        #f.write(test_run_template)

    dagfile = os.path.join(prefix, "dag.sub")
    with io.open(dagfile, 'w') as f:
        f.write(dag_lines)

def wait_till_found(client, path, t_sleep=5):
    print('Waiting for existence of {0}'.format(path))
    found = False
    while not found:
        cmd = "find {0}".format(path)
        print("Remotely executing '{0}'".format(cmd))
        stdin, stdout, stderr = client.exec_command(cmd)
        found = len(stdout.readlines()) > 0
        time.sleep(t_sleep)

def submit(client, rundir, tarname, subfile):
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
    cmd = "condor_q {0}".format(pid)
    print("Remotely executing '{0}'".format(cmd))
    stdin, stdout, stderr = client.exec_command(cmd)
    outlines = stdout.readlines()
    done = False if len(outlines) == 0 else outlines[-1].split()[0] == 'ID'
    return done

def aggregate(client, remotedir, localdir, outdb):
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
    cmd = "rm -rf {0}".format(remotedir)
    print("Remotely executing '{0}'".format(cmd))
    stdin, stdout, stderr = client.exec_command(cmd)
    
def submit_dag(user, host, dbname, solvers, dumpdir, clean):
    timestamp = "_".join([str(t) for t in datetime.now().timetuple()][:-3])

    prompt = "Password for {0}@{1}:".format(user, host)
    pw = getpass.getpass(prompt)
    ssh = pm.SSHClient()
    ssh.set_missing_host_key_policy(pm.AutoAddPolicy())

    outdb = 'out.h5'    
    run_dir = "run_{0}".format(timestamp)
    sub_dir = "/home/{0}/cyclopts-runs".format(user)
    remote_dir = "{0}/{1}".format(sub_dir, run_dir)

    if not os.path.exists(run_dir):
        os.mkdir(run_dir)
    shutil.copy(dbname, run_dir)

    subfile = "dag.sub"
    gen_files(prefix=run_dir, solvers=solvers, db=dbname, subfile=subfile)
    tarname = "{0}.tar.gz".format(run_dir)
    with tarfile.open(tarname, 'w:gz') as f:
        f.add(run_dir)
    shutil.rmtree(run_dir)
    
    print("connecting to {0}@{1}".format(user, host))
    ssh.connect(host, username=user, password=pw)
    pid = submit(ssh, sub_dir, tarname, subfile)
    ssh.close()

    done = False
    while not done:
        print("Querying status of {0}".format(run_dir))
        print("connecting to {0}@{1}".format(user, host))
        ssh.connect(host, username=user, password=pw)
        done = check_finish(ssh, pid)
        ssh.close()
        time.sleep(20)

    print("{0} has completed.".format(run_dir))

    # create dump directory with aggregate input
    if not os.path.exists(dumpdir):
        os.mkdir(dumpdir)
    shutil.copy(dbname, dumpdir)
    
    # aggregate and dump output
    ssh.connect(host, username=user, password=pw)
    print("connecting to {0}@{1}".format(user, host))
    aggregate(ssh, remote_dir, dumpdir, outdb)
    if clean:
        cleanup(ssh, remote_dir)
    ssh.close()

