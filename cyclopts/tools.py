"""Provides some useful tools for working with Cyclopts, including reporting
output.

:author: Matthew Gidden <matthew.gidden _at_ gmail.com>
"""
from __future__ import print_function

import os
import io
import uuid
import shutil
import operator
import tables as t
import numpy as np
from functools import reduce
from itertools import product
from collections import defaultdict, Iterable
import paramiko as pm
from os import kill
from signal import alarm, signal, SIGALRM, SIGKILL
from subprocess import PIPE, Popen
import getpass

import cyclopts
from cyclopts.params import CONSTR_ARGS, Param, BoolParam, SupConstrParam, CoeffParam, \
    ReactorRequestSampler, ReactorRequestBuilder #, ReactorSupplySampler

cyclopts_remote_run_dir = 'cyclopts-runs'

class NotSpecified(object):
    """A helper class singleton for run control meaning that a 'real' value
    has not been given."""
    def __repr__(self):
        return "NotSpecified"

NotSpecified = NotSpecified()

#
# Run Control
#
# Code basis taken from xdress' run control in xdress/utils.py.
#  
class RunControl(object):
    """A composable configuration class for cyclopts. Unlike argparse.Namespace,
    this keeps the object dictionary (__dict__) separate from the run control
    attributes dictionary (_dict). Modified from xdress' run control in
    xdress/utils.py"""

    def __init__(self, **kwargs):
        """Parameters
        -------------
        kwargs : optional
            Items to place into run control.

        """
        self._dict = {}
        for k, v in kwargs.items():
            setattr(self, k, v)
        self._updaters = {}

    def __getattr__(self, key):
        if key in self._dict:
            return self._dict[key]
        elif key in self.__dict__:
            return self.__dict__[key]
        elif key in self.__class__.__dict__:
            return self.__class__.__dict__[key]
        else:
            msg = "RunControl object has no attribute {0!r}.".format(key)
            raise AttributeError(msg)

    def __setattr__(self, key, value):
        if key.startswith('_'):
            self.__dict__[key] = value
        else:
            if value is NotSpecified and key in self:
                return
            self._dict[key] = value

    def __delattr__(self, key):
        if key in self._dict:
            del self._dict[key]
        elif key in self.__dict__:
            del self.__dict__[key]
        elif key in self.__class__.__dict__:
            del self.__class__.__dict__[key]
        else:
            msg = "RunControl object has no attribute {0!r}.".format(key)
            raise AttributeError(msg)

    def __iter__(self):
        return iter(self._dict)

    def __repr__(self):
        keys = sorted(self._dict.keys())
        s = ", ".join(["{0!s}={1!r}".format(k, self._dict[k]) for k in keys])
        return "{0}({1})".format(self.__class__.__name__, s)

    def _pformat(self):
        keys = sorted(self._dict.keys())
        f = lambda k: "{0!s}={1}".format(k, pformat(self._dict[k], indent=2))
        s = ",\n ".join(map(f, keys))
        return "{0}({1})".format(self.__class__.__name__, s)

    def __contains__(self, key):
        return key in self._dict or key in self.__dict__ or \
                                    key in self.__class__.__dict__

    def __eq__(self, other):
        if hasattr(other, '_dict'):
            return self._dict == other._dict
        elif isinstance(other, Mapping):
            return self._dict == other
        else:
            return NotImplemented

    def __ne__(self, other):
        if hasattr(other, '_dict'):
            return self._dict != other._dict
        elif isinstance(other, Mapping):
            return self._dict != other
        else:
            return NotImplemented

    def _update(self, other):
        """Updates the rc with values from another mapping.  If this rc has
        if a key is in self, other, and self._updaters, then the updaters
        value is called to perform the update.  This function should return
        a copy to be safe and not update in-place.
        """
        if hasattr(other, '_dict'):
            other = other._dict
        elif not hasattr(other, 'items'):
            other = dict(other)
        for k, v in other.items():
            if v is NotSpecified:
                pass
            elif k in self._updaters and k in self:
                v = self._updaters[k](getattr(self, k), v)
            setattr(self, k, v)

def parse_rc(files):
    """Parse a list of rc files.

    Parameters
    ----------
    files : list or str
        the files to parse
    """
    files = [files] if isinstance(files, basestring) else files
    rc = RunControl()
    for rcfile in files:
        if not os.path.isfile(rcfile):
            continue
        rcdict = {}
        exec_file(rcfile, rcdict, rcdict)
        rc._update(rcdict)
    return rc

def exec_file(filename, glb=None, loc=None):
    """A function equivalent to the Python 2.x execfile statement."""
    with io.open(filename, 'r') as f:
        src = f.read()
    exec(compile(src, filename, "exec"), glb, loc)
        
class SamplerBuilder(object):
    """A helper class to build configure instances of parameter samplers
    """
    def build(self, rc):
        """Builds all permutations of samplers.

        Parameters
        ----------
        rc : RunControl
            A RunControl object defined by the user's parsed rc file.
        """
        params_dict = self._parse(rc)
        return self._build(params_dict)
    
    def _build(self, params_dict):
        params_list = self._constr_params(params_dict)
        n_samplers = reduce(operator.mul, (len(l) for _, l in params_list), 1)
        samplers = [ReactorRequestSampler() for i in range(n_samplers)]
        ## for supply implementation
        # samplers = [ReactorRequestSampler() if params_dict['request'] \
        #                 else ReactorSupplySampler() for range(n_samplers)]
        self._add_params(samplers, params_list)
        return [sampler for sampler in samplers if sampler.valid()]

    def _parse(self, rc):
        """Provides a dictionary of parameter names to all constructor arguments
        for a resource exchange range of instances.
        
        Parameters
        ----------
        rc : RunControl
            A RunControl object defined by the user's parsed rc file.
        
        Returns
        -------
        params_dict : dict
            A dictionary whose keys are parameter names and values are lists of
            ranges of constructor arguments.
        """
        params_dict = {}
        s = ReactorRequestSampler() # only works for reactor requests for now
        for k, v in rc._dict.items():
            name = k
            attr = v
            if hasattr(s, name):
                vals = []
                args = CONSTR_ARGS[type(getattr(s, name))]
                for arg in args:
                    if arg in attr:
                        vals += [attr[arg]]
                if len(vals) > 0:
                    params_dict[name] = vals
            else:
                print("Found an entry named {0} that "
                      "is unknown to the parser.".format(k))
                
        # for name in s.__dict__:
        #     if hasattr(rc, name):
        #         vals = []
        #         args = CONSTR_ARGS[type(getattr(s, name))]
        #         attr = getattr(rc, name)
        #         for arg in args:
        #             if arg in attr:
        #                 vals += [attr[arg]]
        #         if len(vals) > 0:
        #             params_dict[name] = vals
        return params_dict
        
    def _constr_params(self, params_dict):
        """Returns input for _add_subtree() given input for build()"""
        params_dict = {k: [i for i in product(*v)] \
                           for k, v in params_dict.items()}
        s = ReactorRequestSampler()
        return [(k, [type(getattr(s, k))(*args) for args in v]) \
                    for k, v in params_dict.items()]

    def _add_params(self, samplers, params_list):
        """Configures samplers with all possible perturbations of parameters."""
        pairings = [[(name, param) for param in params] for name, params in params_list]
        perturbations = [p for p in product(*pairings)]
        for i in range(len(perturbations)):
            for name, param in perturbations[i]:
                setattr(samplers[i], name, param)

def merge_leaf(node, dest_file):
    src = node
    dest = dest_file.get_node(node._v_pathname)
    if isinstance(node, t.Table):
        dtypes = src.dtype.names    
        # this is a hack because appending rows throws an error
        # see http://stackoverflow.com/questions/17847587/pytables-appending-recarray
        # dest.append([row for row in src.iterrows()])
        for src_row in src.iterrows():
            dest_row = dest.row
            for j in range(len(dtypes)):
                dest_row[dtypes[j]] = src_row[j]
            dest_row.append()
        dest.flush()
        
def merge_node(node, dest_file):
    if not dest_file.__contains__(node._v_pathname):
        node._v_file.copy_node(
            node._v_pathname, 
            newparent=dest_file.get_node(node._v_parent._v_pathname),
            recursive=True)
        dest_file.flush()
        return 

    if isinstance(node, t.Leaf):
        merge_leaf(node, dest_file)
    else:
        for child in node._v_children:
            merge_node(node._v_file.get_node(node._v_pathname + '/' + child), 
                       dest_file)
            
def combine(files, new_file=None, clean=False):
    """Combines two or more databases with identical layout, writing their
    output into a new file or appending to the first in the list.
    
    Parameters
    ----------
    files : iterator
        An iterator listing all databases to combine
    new_file : str, optional
        The new database to write to. If None, all databases are appended to the
        end of the first database in the list.
    clean : bool, optional
        Whether to remove original files after combining them
    """ 
    if new_file is not None and os.path.exists(new_file):
        raise ValueError('Cannot write combined hdf5 files to an existing location.')

    first = files.next()
    if new_file is not None:
        shutil.copyfile(first, new_file)
        fname = new_file
        if clean:
            os.remove(first)
    else:
        fname = first

    aggdb = t.open_file(fname, 'a')
    for f in files:
        db = t.open_file(f, 'r')
        merge_node(db.root, aggdb)
        aggdb.flush()
        db.close()
        if clean:
            os.remove(f)
    aggdb.close()

def run(args, cwd = None, shell = False, kill_tree = True, timeout = -1, env = None):
    '''
    Run a command with a timeout after which it will be forcibly
    killed.
    '''
    class Alarm(Exception):
        pass
    def alarm_handler(signum, frame):
        raise Alarm
    p = Popen(args, shell = shell, cwd = cwd, stdout = PIPE, stderr = PIPE, env = env)
    if timeout != -1:
        signal(SIGALRM, alarm_handler)
        alarm(timeout)
    try:
        stdout, stderr = p.communicate()
        if timeout != -1:
            alarm(0)
    except Alarm:
        pids = [p.pid]
        if kill_tree:
            pids.extend(get_process_children(p.pid))
        for pid in pids:
            # process might have died before getting to this line
            # so wrap to avoid OSError: no such process
            try: 
                kill(pid, SIGKILL)
            except OSError:
                pass
        return -9, '', ''
    return p.returncode, stdout, stderr

def get_process_children(pid):
    p = Popen('ps --no-headers -o pid --ppid %d' % pid, shell = True,
              stdout = PIPE, stderr = PIPE)
    stdout, stderr = p.communicate()
    return [int(p) for p in stdout.split()]

def ssh_test_connect(client, host, user, keyfile=None, auth=True):
    """Tests an ssh connection and returns success or failure thereof.
    
    Parameters
    ----------
    client : paramiko SSH client
    host : str
    user : str
    keyfile : str, optional
    auth : bool, optional
        whether to prompt for a password authorization on failure
    """
    keyfile = keyfile if keyfile is not None else \
        os.path.join(os.environ['HOME'], '.ssh','id_rsa.pub') 

    try:
        client.connect(host, username=user, key_filename=keyfile)
        client.close()
        can_connect = True
    except pm.AuthenticationException:
            can_connect = False
    except pm.BadHostKeyException:
            import pdb; pdb.set_trace()
            can_connect = False
    password = None
    if not can_connect and auth:
        password = False
        while not password:
            password = getpass.getpass("{0}@{1} password: ".format(user, host))
            # pub = pm.ssh_pub_key(keyfile)
            # cmds = ["mkdir -p ~/.ssh",
            #         'echo "{0}" >> ~/.ssh/authorized_keys'.format(pub),
            #         'chmod og-rw ~/.ssh/authorized_keys',
            #         'chmod a-x ~/.ssh/authorized_keys',
            #         'chmod 700 ~/.ssh',
            #         ]
            client.connect(host, username=user, password=password)
            # for cmd in cmds:
            #     stdin, stdout, stderr = client.exec_command(cmd)
            # client.close()
            # # verify thatthis key works
            # client.connect(host, username=user, key_filename=keyfile)
            # client.close()
            can_connect = True
            print("finished connecting")
    return can_connect, keyfile, password
