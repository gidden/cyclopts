from __future__ import print_function

import warnings
import tables as t
import shutil
import time
import os
import io
import glob 
import uuid
import re

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

tar_output_cmd = """cd {remotedir} && tar -czf {tardir}.tar.gz {re}"""

def _get_files(client, remotedir, localdir, re, verbose=False):
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
    verbose : str, optional
        print information about the command
    """
    tardir = 'outfiles'
    cmd = tar_output_cmd.format(remotedir=remotedir, tardir=tardir, re=re)
    exec_remote_cmd(client, cmd, verbose=verbose)
    
    remotetar = os.path.join(remotedir, '{0}.tar.gz'.format(tardir))
    localtar = os.path.join(localdir, '{0}.tar.gz'.format(tardir))
    ftp = client.open_sftp()
    if verbose:
        print("Copying {0} from condor submit node to {1}.".format(
                remotetar, localtar))
    ftp.get(remotetar, localtar)
    ftp.close()

    with tarfile.open(localtar, 'r:gz') as f:
        files = f.getnames()
        nfiles = len(files)
        f.extractall(localdir)

    if verbose:
        print("retrived {0} files from tarball".format(nfiles))

    os.remove(localtar)
    return nfiles

def exec_remote_cmd(client, cmd, t_sleep=5, verbose=False):
    """A wrapper function around paramiko.client.exec_command that helps with
    error handling and returns only once the command has been completed.

    Parameters
    ----------
    client : paramiko ssh client
        the client to use
    cmd : str
        the command to execute
    t_sleep : float, optional
        the amount of time to wait between querying if a job is complete
    verbose : str, optional
        print information about the command
    """
    if verbose:
        print("Remotely executing '{0}'".format(cmd))
    stdin, stdout, stderr = client.exec_command(cmd)
    while not stdout.channel.exit_status_ready():
        if verbose:
            print('Command not complete, checking again in {0} seconds.'.format(
                    t_sleep))
        time.sleep(t_sleep)
    if stdout.channel.recv_exit_status() != 0:
        raise IOError('Error with command {0}: {1}'.format(
                cmd, " ".join(stderr)))
    return stdin, stdout, stderr

def rm(user, host="submit-3.chtc.wisc.edu", keyfile=None, expr=None, 
       verbose=False):
    """Remove condor jobs on a remote machine.
    
    Parameters
    ----------
    user : str
        the remote machine user name
    host : str, optional
        the remote machine host
    keyfile : str, optional
        a SSH private key file to use
    expr : str, optional
        an expression used to search for jobs
    verbose : str, optional
        print information    
    """
    client = pm.SSHClient()
    client.set_missing_host_key_policy(pm.AutoAddPolicy())
    _, keyfile, pw = tools.ssh_test_connect(client, host, user, keyfile=keyfile, 
                                            auth=False)
    client.connect(host, username=user, key_filename=keyfile, password=pw)
    print("connecting to {0}@{1}".format(user, host))
    
    cmd = "condor_q {user}".format(user=user)
    stdin, stdout, stderr = exec_remote_cmd(client, cmd, verbose=verbose)
    
    expr = user if expr is None else expr
    cexpr = re.compile(expr)
    pids = [l.split()[0] for l in stdout.readlines() if cexpr.search(l)]
    
    if len(pids) > 0:
        cmd = "condor_rm {pids}".format(pids=" ".join(pids))
        stdin, stdout, stderr = exec_remote_cmd(client, cmd, verbose=verbose)
    else:
        print("No jobs found matching {0}.".format(expr))
    client.close()
        
def collect(localdir, remotedir, user, host="submit-3.chtc.wisc.edu", 
            outdb='cyclopts_results.h5', clean=False, keyfile=None,
            verbose=False):
    """Collects all cyclopts output on a remote site and collapses it into a
    single data base on a local machine.
    
    Parameters
    ----------
    localdir : str
        the directory to place output on the local machine
    remotedir : str
        the directory on the remote machine
    user : str
        the remote machine user name
    host : str, optional
        the remote machine host
    outdb : str, optional
        the name of the database file to to be used on the local machine
    clean : bool, optional
        whether or not to clean up the remote machine
    keyfile : str, optional
        a SSH private key file to use
    verbose : str, optional
        print information
    """
    client = pm.SSHClient()
    client.set_missing_host_key_policy(pm.AutoAddPolicy())
    _, keyfile, pw = tools.ssh_test_connect(client, host, user, keyfile, auth=True)

    client.connect(host, username=user, key_filename=keyfile, password=pw)
    print("connecting to {0}@{1}".format(user, host))

    if not os.path.exists(localdir):
        os.makedirs(localdir)    

    # get files and clean up
    nfiles = _get_files(client, remotedir, localdir, '*_out.h5')
    
    if clean:
        cmd = "rm -r {0} && rm {0}.tar.gz".format(remotedir)
        stdin, stdout, stderr = exec_remote_cmd(client, cmd, verbose=verbose)
    client.close()
    
    # combine files and clean up
    files = glob.iglob(os.path.join(localdir, '*_out.h5'))
    stmt = "Combining {0} databases into {1}".format(nfiles, outdb)
    print(stmt)
    tools.combine(files, new_file=outdb, clean=True)
