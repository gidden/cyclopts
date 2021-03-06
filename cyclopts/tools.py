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
from collections import defaultdict, Iterable, Sequence, Mapping
import paramiko as pm
from os import kill
from signal import alarm, signal, SIGALRM, SIGKILL
from subprocess import PIPE, Popen
import getpass
import importlib
import itertools as itools
import gc
import resource

import cyclopts
from cyclopts.params import PARAM_CTOR_ARGS, Param, BoolParam, SupConstrParam, \
    CoeffParam

FILTERS = t.Filters(complevel=4)

cyclopts_remote_run_dir = 'cyclopts-runs'

class Incrementer(object):
    """A simple helper class to increment a value"""
    def __init__(self, start = 0):
        """Parameters
        ----------
        start : int, optional
            an initial value
        """
        self._val = start - 1

    def next(self):
        """Returns an incremented value"""
        self._val += 1
        return self._val

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

    Returns
    -------
    rc : RunControl
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
    """A function equivalent to the Python 2.x execfile statement. Taken from
    xdress/utils.py"""
    with io.open(filename, 'r') as f:
        src = f.read()
    exec(compile(src, filename, "exec"), glb, loc)

def _merge_leaf(node, dest_file):
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
    
def _copy_node(node, dest_file, recursive=False):
    if node._v_depth == 0: # base recursion level, don't copy root
        return
    
    if dest_file.__contains__(node._v_pathname):
        return

    parent = node._v_parent
    if not dest_file.__contains__(parent._v_pathname):
        _copy_node(parent, dest_file) # parent doesn't exist, copy it

    # copy node
    node._v_file.copy_node(
        node._v_pathname, 
        newparent=dest_file.get_node(node._v_parent._v_pathname),
        recursive=recursive)
    dest_file.flush()
        
def _merge_node(node, dest_file):
    if not dest_file.__contains__(node._v_pathname):
        _copy_node(node, dest_file, recursive=True)
        return 

    if isinstance(node, t.Leaf):
        _merge_leaf(node, dest_file)
    else:
        for child in node._v_children:
            _merge_node(node._v_file.get_node(node._v_pathname + '/' + child), 
                        dest_file)
            
def combine(files, new_file=None, clean=False, verbose=False):
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
    verbose : bool, optional
        Whether to print output
    """ 
    if new_file is not None and os.path.exists(new_file):
        raise ValueError('Cannot write combined hdf5 files to an existing location.')

    first = files.next()
    if new_file is not None:
        if verbose:
            print('Starting with base file {0}'.format(first))
        shutil.copyfile(first, new_file)
        fname = new_file
        if clean:
            os.remove(first)
    else:
        fname = first

    aggdb = t.open_file(fname, 'a')
    for f in files:
        if verbose:
            print('Merging {0}'.format(f))
        db = t.open_file(f, 'r')
        _merge_node(db.root, aggdb)
        aggdb.flush()
        db.close()
        if clean:
            os.remove(f)
    aggdb.close()

def get_process_children(pid):
    """Return 
    ------
    children : list of ints
        all of a processes' children
    """
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
        [os.path.join(os.environ['HOME'], '.ssh','id_rsa'),
         os.path.join(os.environ['HOME'], '.ssh','chtckey')]

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

def str_to_uuid(x):
    """return a uuid from a stored value, allows strings of len == 15 which is 
    missing a null-padded value"""
    if len(x) < 16:
        while len(x) < 16:
            x += '\0'
    return uuid.UUID(bytes=x)     

def uuid_to_str(x):
    """return a string of a uuid, needed in case the uuid is missing a null-
    padded value"""
    ret = x.hex
    if len(ret) < 16:
        while len(ret) < 16:
            ret += '\0'
    return ret

def uuidhex(bytes=bytes):
    return uuid.UUID(bytes=bytes).hex

def memusg(pid):
    """in kb"""
    # could also use 
    # resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    fname = os.path.join(os.path.sep, 'proc', str(pid), 'status')
    with io.open(fname) as f:
        lines = f.readlines()
    return float(next(l for l in lines if l.startswith('VmSize')).split()[1])

def attr_from_sources(attr, sources):
    """Returns an attribute from a priority queue of sources, returns None if no
    source has that attribute"""
    for source in sources:
        if hasattr(source, attr) and getattr(source, attr) is not None:
            return getattr(source, attr)
    return None

def all_obj_rcs(rc=None, args=None):
    """Return all run control files in priority order known to cyclopts"""
    ret = []
    if rc is not None:
        ret.append(rc)
    if args is not None and hasattr(args, 'cycrc') and os.path.exists(args.cycrc):
        ret.append(parse_rc(args.cycrc))
    check = os.path.expanduser('~/.cycloptsrc.py')
    if os.path.exists(check):
        ret.append(parse_rc(check))
    return ret

def obj_info(kind=None, rcs=None, args=None):
    """Get information about an importable object

    Parameters
    ----------
    kind : str
        the kind of object
    rcs : list of RunControl objects or single object, optional
        rcs are checked in order
    args : argparse args, optional
        CLI args
    
    Return
    ------
    info : tuple of package, module, and class names
    """
    mod, cname, pack = None, None, None
    rcs = [rcs] if not isinstance(rcs, list) else rcs
    sources = [args] + rcs # try CLI first, then rcs in order
    attrs = ['{0}_package'.format(kind), '{0}_module'.format(kind), 
             '{0}_class'.format(kind)]
    return tuple(attr_from_sources(x, sources) for x in attrs)
    
def get_obj(kind=None, rcs=None, args=None):
    """Get an object of certain kind, e.g. species or family. Both the rc and
    args argument will be searched for attributes named <kind>_package,
    <kind>_module, and <kind>_cname. The package/module is then imported and an
    instance of the cname is returned. The CLI is searched before the rcs.

    Parameters
    ----------
    kind : str
        the kind of object
    rcs : list of RunControl objects or single object, optional
        rcs are checked in order
    args : argparse args, optional
        CLI args

    Return
    ------
    inst : an object instance
    """
    pack, mod, cname = obj_info(kind=kind, rcs=rcs, args=args)
    
    try:
        mod = importlib.import_module(mod, package=pack)
    except AttributeError:
        raise RuntimeError('Could not find {0} module {1}. Make sure to add '
                           'a {0}_module entry to a run control file or the '
                           'CLI.'.format(kind, mod))
    
    if cname is None or not hasattr(mod, cname):
        raise RuntimeError('Could not find {0} class {1}. Make sure to add '
                           'a {0}_class entry to a run control file or the '
                           'CLI.'.format(kind, cname))
    
    inst = getattr(mod, cname)() 
    return inst
        
def collect_instids(h5file, path, rc=None, instids=None, colname='instid'):
    """Collects all instids as specified. 
    
    If rc and instids is None, all ids found in the h5file's path are collected.
    Otherwise, instids provided by the instid listing and the paramater space
    defined by the run control `inst_queries` parameter are collected.

    Parameters
    ----------
    h5file : PyTables File object
        the file to collect ids from
    path : str
        the path to a property table node
    rc : RunControl object, optional
        a run control object specifying a subset of instids to collect
    instids : collection of uuids
        explicit instids to collect
    colname : str
        the instance id column name

    Return
    ------
    instids : set of uuids
    """
    instids = set(instids) if instids is not None else set()
    rc = rc if rc is not None else RunControl()
    instids |= set(uuid.UUID(x) for x in rc.inst_ids) \
        if 'inst_ids' in rc else set()
    
    # inst queries are a mapping from instance table names to queryable
    # conditions, the result of which is a collection of instids that meet those
    # conditions
    h5node = h5file.get_node(path)
    conds = rc.inst_queries if 'inst_queries' in rc else []
    if isinstance(conds, basestring):
        conds = [conds]
    if len(conds) > 0:
        ops = conds[1::2]
        conds = ['({0})'.format(c) if \
                     not c.lstrip().startswith('(') and \
                     not c.rstrip().endswith(')') else c for c in conds[::2]]
        cond = ' '.join(
            [' '.join(i) for i in \
                 itools.izip_longest(conds, ops, fillvalue='')]).strip()
        vals = [x[colname] for x in h5node.where(cond)]
        vals = [str_to_uuid(x) for x in vals]
        instids |= set(vals)
        
    # if no ids, then run everything
    if len(instids) == 0:
        for row in h5node.iterrows():
            instids.add(str_to_uuid(row[colname]))
    
    return instids

"""simple utility for determining if something is a sequence (and not a
string)"""
seq_not_str = lambda obj: isinstance(obj, Sequence) \
    and not isinstance(obj, basestring)

def n_permutations(x, iter_keys=[], recurse=True):
    """Parameters
    ----------
    x : dict, list, or other
    iter_keys : a list of keys atomic values should be iterables, optional
    recurse : bool, whether to recurse at the lowest level
    
    Returns
    -------
    n : int
        the total number of permutations of values in x, if x has 
        container values, those are recusively interrogated as well
    """
    n = 1
    if seq_not_str(x):
        if seq_not_str(x[0]):
            if recurse:
                for y in x:
                    n *= n_permutations(y, recurse=recurse)
            else:
                n *= len(x)
        else:
            factor = len(x) if recurse else 1
            n *= factor
    elif isinstance(x, Mapping):
        for k, v in x.items():
            flag = False if k in iter_keys else True # in blacklist
            n *= n_permutations(v, recurse=flag)
    return n

def expand_args(x):
    """Parameters
    ----------
    x : list of lists of arguments
    
    Returns
    -------
    args : generator
        a generator that returns a collection of single arguments
    """
    for y in itools.product(*x):
        yield y

def conv_insts(fam, fam_io_manager, sp, sp_io_manager, 
               ninst=1, update_freq=100, verbose=False):
    n = 0
    for point in sp.points():
        param_uuid = uuid.uuid4()
        sp.record_point(point, param_uuid, sp_io_manager)
        for i in range(ninst):
            inst_uuid = uuid.uuid4()
            inst = sp.gen_inst(point, inst_uuid, sp_io_manager)
            fam.record_inst(inst, inst_uuid, param_uuid, sp.name, 
                            fam_io_manager)
            if n % update_freq == 0:
                if verbose:
                    # print('Total writes: {0}'.format(
                    #         sum([tbl.n_writes for tbl in fam_tables.values() + sp_tables.values()])))
                    print('Memusg before collect: {0}'.format(
                            resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
                gc.collect()
                if verbose:
                    print('Memusg after collect: {0}'.format(
                            resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
                    print('{0} instances have been converted'.format(n))
            n += 1
    
    if verbose:
        print('{0} instances have been converted'.format(n))

def cyc_members(obj):
    """return a list of persistable members per the Cyclopts style guide."""
    members = obj.__class__.__dict__.keys()
    cycfilter = lambda x: x.startswith('_') or x.endswith('_') or x[0].isupper()
    return [x for x in members if not cycfilter(x)]

def fam_and_sp(args):
    rc = parse_rc(args.rc) if hasattr(args, 'rc') else None
    if hasattr(args, 'cycrc'):
        obj_rcs = [rc, parse_rc(args.cycrc)] \
            if os.path.exists(args.cycrc) else [rc]
    sp = get_obj(kind='species', rcs=obj_rcs, args=args)
    fam = sp.family
    return fam, sp

def drive_post_process(res_tbl, 
                       fam=None, fam_io_managers=None, 
                       sp=None, sp_io_managers=None,
                       verbose_freq=None, limit=None):
    iid_to_sids = res_tbl.value_mapping('instid', 'solnid', uuids=True)
    niids = len(iid_to_sids.keys())
    count = 0
    verbose = verbose_freq is not None
    for iid, sids in iid_to_sids.items():
        if verbose:
            if count % verbose_freq == 0:
                print('{0}/{1} instances have been post processed.'.format(
                        count, niids))
            if count == limit:
                return # early exit
            count += 1
        props = None
        if fam is not None:
            props = fam.post_process(iid, sids, fam_io_managers)
        if sp is not None:
            sp.post_process(iid, sids, props, sp_io_managers)

def col2grp(in_old, out_old, in_new, out_new):    
    """Make old input/output files using a columnar id-based schema into a group
    id-based schema. Currently only works for ExchangeFamily and
    StructuredSpecies."""
    in_old = t.open_file(in_old, mode='r')
    out_old = t.open_file(out_old, mode='r')
    in_new = t.open_file(in_new, mode='w')
    out_new = t.open_file(out_new, mode='w')

    # setup tables
    arctbl = in_old.root.Species.StructuredRequest.Arcs \
        if in_old.__contains__('/Species/StructuredRequest') else \
        in_old.root.Species.StructuredSupply.Arcs

    all_tbls = {in_new: [in_old.root.Family.ResourceExchange.ExchangeArcs,
                         arctbl,],
                out_new: [out_old.root.Family.ResourceExchange.ExchangeInstSolutions,]}

    old_files = {in_new: in_old,
                 out_new: out_old}
    
    for h5f, tbls in all_tbls.items():
        pths = [x._v_pathname for x in tbls]
        oldf = old_files[h5f]
        for node in oldf.walk_nodes(classname='Leaf'):
            pth = node._v_pathname
            if pth not in pths:
                _copy_node(oldf.get_node(pth), h5f)
    
    for h5f, tbls in all_tbls.items():
        for tbl in tbls:
            dtype = np.dtype(tbl.dtype.descr[1:])
            path = tbl._v_pathname
            colid = ''
            ntbl = None
            _copy_node(tbl._v_parent, h5f)
            h5f.create_group(tbl._v_parent._v_pathname, tbl._v_name, 
                             filters=FILTERS)
            for x in tbl.iterrows():
                y = str_to_uuid(x[0]).hex
                if y != colid:
                    if ntbl is not None:
                        ntbl.flush()
                    colid = y
                    ntbl = cyclopts.cyclopts_io.Table(h5f, '/'.join([path, 'id_'+colid]), dt=dtype)
                    ntbl.create()
                # either do [x[1:]] or append
                ntbl.append_data([x[1:]])
            ntbl.flush()
            
    in_old.close()
    out_old.close()
    in_new.close()
    out_new.close()

def masked_filter(c, mask, unmask=False):
    """Return a subset of a collection with a mask applied"""
    if not unmask:
        return [c[i] for i in range(len(c)) if mask[i]]
    else:
        return [c[i] for i in range(len(c)) if not mask[i]]

# def run_insts_mp():
#     q = mp.Queue()
#     pool = mp.Pool(4, multi_proc_gen, (q,))
#     lock = mp.Lock()
#     for point in sp.points():
#         param_uuid = uuid.uuid4()
#         if lock is not None:
#             lock.acquire()
#         sp.record_point(point, param_uuid, sp_manager.tables)
#         if lock is not None:
#             lock.release()
#         for i in range(ninst):
#             inst_uuid = uuid.uuid4()
#             # q.put((inst_uuid, param_uuid, point, sp, fam, 
#             #        fam_manager.tables, lock))
#             q.put((inst_uuid, param_uuid, lock))
            
#     while not q.empty():
#         if verbose and q.qsize() % update_freq == 0:
#             print('{0} instances have been converted'.format(n))
#         time.sleep(1)

