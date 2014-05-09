from __future__ import print_function

import paramiko as pm
import tables as t
import tarfile
import shutil
from datetime import datetime
import getpass
import time

rc_template = """
path = {0} 
rows = range({1}, {2})
"""

sub_template = """
universe = vanilla
executable = run.sh
arguments = {0}
output = {0}.out
error = {0}.err
log = {0}.log
requirements = (OpSysAndVer =?= "SL6") && Arch == "X86_64"
should_transfer_files = YES
when_to_transfer_output = ON_EXIT
transfer_input_files = ../cyclopts-build.tar.gz, {1}, {0}.rc
request_cpus = 1
request_memory = 2500
request_disk = 10242880
notification = never
"""

run_template = """
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

dag_template = """JOB J_{0} {0}.sub\n"""

def gen_files(prefix=".", db="in.h5", tbl="ReactorRequestSampler", subfile = "dag.sub"):
    """Generates all files needed to run a DAGMan instance of the given input
    database.
    """
    h5file = t.open_file(db, mode='r')
    if hasattr(h5file.root, tbl):
        tbl = getattr(h5file.root, tbl)
    else:
        raise IOError("Can't find table with name {0}.".format(tbl))
    nrows = tbl.nrows()
    h5file.close()
    
    print("generating files for {0} runs".format(nrows))
    dag_lines = ""
    for i in range(len(nrows)):
        rcname = os.path.join(prefix, "{0}.rc".format(i))
        with io.open(rcname, 'w') as f:
            f.write(rc_template.format(tbl, i, i+1))
        rcfiles.append(rcname)
        subname = os.path.join(prefix, "{0}.sub".format(i))
        with io.open(subname, 'w') as f:
            f.write(sub_template.format(i, db))
        subfiles.append(subname)
        dag_lines += dag_template.format(i)
    
    runfile = os.path.join(prefix, "run.sh")
    with io.open(runfile, 'w') as f:
        f.write(run_template.format(db))
    dagfile = os.path.join(prefix, "dag.sub")
    with io.open("dag.sub", 'w') as f:
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
    ftp.put(tarname, ".")
    ftp.close()

    cmd = "tar -xf {0}; cd {1}; condor_sumbit_dag {2};".format(
        tarname, tarname.split(".tar.gz")[0], subfile)
    ssh.exec_command(cmd)

    ssh.close()

def check_finish(user, host, pw, dirname, subfile):
    user = user
    host = host
    pw = pw
    ssh = pm.SSHClient()
    ssh.set_missing_host_key_policy(pm.AutoAddPolicy())
    print("connecting to {0}@{1}".format(user, host))
    ssh.connect(host, username=user, password=pw)

    checkfile = "{0}.dagman.out".format(subfile)
    cmd = "head {0}/{1}".format(dirname, subfile)
    stdin, stdout, stderr = ssh.exec_command(cmd)
    pid = std.out.readlines()[1].split('condor_scheduniv_exec.').split()[0]
    cmd = "condor_q {0}".format(pid)
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
    
    if not os.path.exists(dumpdir):
        os.mkdir(dumpdir)

    ftp = ssh.open_sftp()
    ftp.get("{0}/{1}".format(dirname, "*_out.h5"), dumpdir)
    ftp.close()
    
    cmd = "rm -rf {0}".format(dirname)
    stdin, stdout, stderr = ssh.exec_command(cmd)

    ssh.close()

def condor(user, host, dbname, dumpdir, clean):
    pw = getpass.getpass()

    dirname = "run_{0}".format(
        "_".join([str(t) for t in datetime.now().timetuple()][:-4]))

    os.mkdir(dirname)
    shutil.copyfile(dbname, dirname)
    subfile = "dag.sub"
    gen_files(prefix=dirname, db=dbname, subfile=subfile)
    tarname = "{0}.tar.gz".format(dirname)
    with tarfile.open(tarname, 'w:gz') as f:
        f.add(dirname)
    os.removedirs(dirname)
    
    submit(user, host, pw, tarname, subfile)

    done = False
    while not done:
        done = check_finish(user, host, pw, dirname, subfile)
        time.sleep(300)

    if clean:
        cleanup(user, host, pw, dirname, dumpdir)

if __name__ == "__main__":
    condor()
