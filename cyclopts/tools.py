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

import cyclopts
from cyclopts.params import CONSTR_ARGS, Param, BoolParam, SupConstrParam, CoeffParam, \
    ReactorRequestSampler, ReactorRequestBuilder #, ReactorSupplySampler

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

class SolverDesc(t.IsDescription):
    sim_id = t.StringCol(36) # len(str(uuid.uuid4())) == 36
    type = t.StringCol(12)

class GraphDesc(t.IsDescription):
    graph_id = t.StringCol(36)  # len(str(uuid.uuid4())) == 36
    n_supply = t.Int32Col()
    n_request = t.Int32Col()
    n_sup_nodes = t.Int32Col()
    n_req_nodes = t.Int32Col()
    n_arcs = t.Int32Col()

class RRSamplerDesc(t.IsDescription):
    graph_id = t.StringCol(36) # len(str(uuid.uuid4())) == 36
    n_commods = t.Int32Col() 
    n_request = t.Int32Col()
    assem_per_req = t.Int32Col()
    assem_multi_commod = t.Float32Col()
    req_multi_commods = t.Int32Col()
    exclusive = t.Float32Col()
    n_req_constr = t.Int32Col()
    n_supply = t.Int32Col() 
    sup_multi = t.Float32Col()
    sup_multi_commods = t.Int32Col() 
    n_sup_constr = t.Int32Col() 
    sup_constr_val = t.Float32Col()
    connection = t.Float32Col()

# class RSSamplerDesc(t.IsDescription):
#     sim_id = t.StringCol(36) # len(str(uuid.uuid4())) == 36
#     sol_type = t.StringCol(12)

class FlowDesc(t.IsDescription):
    sim_id = t.StringCol(36) # len(str(uuid.uuid4())) == 36
    arc_id = t.Int64Col()
    flow = t.Float64Col()

class SolnDesc(t.IsDescription):
    sim_id = t.StringCol(36) # len(str(uuid.uuid4())) == 36
    graph_id = t.StringCol(36) # len(str(uuid.uuid4())) == 36
    time = t.Float64Col() # in seconds
    obj = t.Float64Col() 
    cyclus_version = t.StringCol(12)
    cyclopts_version = t.StringCol(12)

class Reporter(object):
    
    def report_solver(self, row, sim_id, graph_id, sparams):
        row['sim_id'] = str(sim_id)
        row['type'] = sparams.type
        row.append()

    def report_graph(self, row, sim_id, graph_id, gparams):
        row['graph_id'] = graph_id
        row['n_supply'] = len(gparams.v_nodes_per_sup)
        row['n_request'] = len(gparams.u_nodes_per_req)
        row['n_sup_nodes'] = sum([len(vec) for k, vec in gparams.v_nodes_per_sup.items()])
        row['n_req_nodes'] = sum([len(vec) for k, vec in gparams.u_nodes_per_req.items()])
        row['n_arcs'] = len(gparams.arc_pref)
        row.append()
    
    def report_rr_sampler(self, row, sim_id, graph_id, sampler):
        s = sampler

        params = ['sup_multi_commods',
                  'n_sup_constr',
                  'n_commods', 
                  'n_request',
                  'assem_per_req',
                  'req_multi_commods',
                  'n_req_constr',
                  'n_supply',
                  ]

        bool_params = ['connection',
                       'assem_multi_commod',
                       'exclusive',
                       'sup_multi'
                       ]

        constr_params = ['sup_constr_val']

        row['graph_id'] = graph_id
        for param in params:
            if hasattr(s, param):
                row[param] = getattr(s, param).avg
        for param in bool_params:
            if hasattr(s, param):
                row[param] = getattr(s, param).cutoff
        for param in constr_params:
            if hasattr(s, param):
                row[param] = getattr(s, param).cutoff
        row.append()

    #
    # TO DO
    #
        
    # def report_rs_sampler(self, row, sim_id, graph_id, sampler):
    #     row['sim_id'] = str(sim_id)
    
    def report_flows(self, row, sim_id, graph_id, flows):
        for f in flows:
            row['sim_id'] = str(sim_id)
            row['arc_id'] = f.id
            row['flow'] = f.flow
            row.append()

    def report_solution(self, row, sim_id, graph_id, soln):
        row['sim_id'] = sim_id
        row['graph_id'] = graph_id
        row['time'] = soln[0]
        row['obj'] = soln[1]
        row['cyclus_version'] = soln[2]
        row['cyclopts_version'] = soln[3]
        row.append()
            
def report(sampler, gparams, sparams, soln, sim_id = None, db_path = None):
    """Dumps parameter and solution information to an HDF5 database.
    
    Parameters
    ----------
    sampler : ReactorRequestSampler or ReactorSupplySampler 
        The sampler used to generate the exchange instance
    gparams : GraphParams
        ExchangeGraph-defining parameters
    sparams : SolverParams
        ExchangeSolver-defining parameters
    soln : Solution
        The solved graph's solution.
    sim_id : int, optional
        The simulation id to use in the database. A UUID is generated by 
        default.
    db_path : str, optional
        The database to dump information to. The default is cyclopts.h5 
        file placed in the current working directory.
    """
    db_path = os.path.join(os.getcwd(), 'cyclopts.h5') if db_path is None \
        else db_path
    sim_id = uuid.uuid4().int if sim_id is None else sim_id
    graph_id = str(gparams.id)

    mode = "a" if os.path.exists(db_path) else "w"
    filters = t.Filters(complevel=4)
    h5file = t.open_file(db_path, mode=mode, title="Cyclopts Output", filters=filters)
    
    flows = [ArcFlow(soln.flows[i:]) for i in range(len(soln.flows))]
    #print("nflows:", len(flows))
    obj = sum([f.flow / gparams.arc_pref[f.id] for f in flows])
    solnparams = [soln.time, obj, soln.cyclus_version, cyclopts.__version__]

    tables = [('solver', SolverDesc, 'Solver Params', sparams),
              ('flows', FlowDesc, 'Arc Flows', flows),
              ('solution', SolnDesc, 'Solution Params', solnparams),
              ('graph', GraphDesc, 'Graph Params', gparams),
              ]
    if isinstance(sampler, ReactorRequestSampler):
        tables += [('rr_sampler', RRSamplerDesc, 'Reactor Request Sampling', sampler)]
# TODO
#    elif isinstance(sampler, ReactorSupplySampler):
#        tables += [('rssample', SolnDesc, 'Reactor Supply Params', sampler)]
    else:
        raise TypeError("Sampler is of an unknown type.")

    r = Reporter()
    for name, desc, title, data in tables:
        if not name in h5file.root._v_children:
            h5file.create_table("/", name, desc, title, filters=filters)
        if hasattr(r, 'report_' + name):
            row = h5file.get_node('/' + name).row
            meth = getattr(r, 'report_' + name)
            meth(row, sim_id, graph_id, data)
        
    h5file.close()
            
def combine(files, new_file = None):
    """Combines two or more databases with identical layout, writing their
    output into a new file or appending to the first in the list.
    
    Parameters
    ----------
    files : list
        A list of all databases to combine
    new_file : str, optional
        The new database to write to. If None, all databases are appended to the
        end of the first database in the list.
    """ 
    if len(files) == 0:
        raise ValueError("Must have at least one file to combine.")

    if new_file is not None and os.path.exists(new_file):
        raise ValueError('Cannot write combined hdf5 files to an existing location.')

    if new_file is not None:
        shutil.copyfile(files[0], new_file)

    fname = files[0] if new_file is None else new_file

    f = t.open_file(fname, 'a')
    dbs = [t.open_file(files[i], 'r') for i in range(1, len(files))]
    for db in dbs:
        tbls = [node._v_name for node in db.iter_nodes('/', classname='Table')]
        for tbl in tbls:
            src = db.get_node('/', name=tbl, classname='Table')
            dest = f.get_node('/', name=tbl, classname='Table')
            dtypes = src.dtype.names
            
            # this is a hack because appending rows throws an error
            # see http://stackoverflow.com/questions/17847587/pytables-appending-recarray
            # dest.append([row for row in src.iterrows()])
            for src_row in src.iterrows():
                dest_row = dest.row
                for j in range(len(dtypes)):
                    dest_row[dtypes[j]] = src_row[j]
                dest_row.append()
        db.close()
    f.close()
    
def from_h5(fin=None, subinput=None):
    """Converts an input HDF5 database into a list of Sampler-type objects that
    represent discrete, individual data points in a possibly non-contiguous
    dataspace.

    If subinput is provided, it is read directly. If not, the entire database
    converted.
    
    Parameters
    ----------
    fin : str
        the input file name (*.h5)
    subinput : dict
        a subset of input to read int
    """
    fin = "in.h5" if fin is None else fin
    samplers = []
    fin = t.open_file(fin, mode='r')
    tbls = fin.root._f_list_nodes(classname="Table") \
        if subinput is None else \
        [fin.root._f_get_child(k) for k in subinput.keys()]
    
    for tbl in tbls:
        tblname = tbl._v_name
        print("adding", tblname)
        if not hasattr(cyclopts.params, tblname):
            continue
        start = subinput[tblname][0] if subinput is not None else 0
        stop = subinput[tblname][-1] + 1 if subinput is not None else tbl.nrows
        for row in tbl.iterrows(start=start, stop=stop):
            inst = getattr(cyclopts.params, tblname)()
            inst.import_h5(row)
            samplers.append(inst)
    fin.close()
    return samplers


def exec_from_h5(fin=None, fout=None, rc=None, solvers=None):
    """Runs an instance of Cyclopts.
    
    Parameters
    ----------
    fin : str, optional
        the input file name (*.h5)
    fout : str, optional
        the output file name (*.h5)
    rc : str, optional
        the run control file
    solvers : list, optional
        the solvers to use on each generated instance
    """
    fin = "in.h5" if fin is None else fin
    fout = "out.h5" if fout is None else fout
    solvers = ["cbc"] if solvers is None else solvers
    
    subinput = None
    if rc is not None:
        rcdict = parse_rc(rc)
        subinput = {rcdict.path: rcdict.rows}
        
    samplers = from_h5(fin, subinput)
    execute_cyclopts(samplers, solvers, fout)

def execute_cyclopts(samplers, solvers, db_path): 
    for sampler in samplers:
        for solver in solvers:
            rrb = ReactorRequestBuilder(sampler)
            gparams = rrb.build()
            sparams = SolverParams(solver)
            soln = execute_exchange(gparams, sparams)
            report(sampler, gparams, sparams, soln, db_path=db_path)
