"""Provides some useful tools for working with Cyclopts, including reporting
output.

:author: Matthew Gidden <matthew.gidden@gmail.com>
"""

import os
import uuid
import shutil
import operator
import tables as t
import numpy as np
from functools import reduce
from itertools import product

import cyclopts
from cyclopts.params import CONSTR_ARGS, Param, BoolParam, SupConstrParam, CoeffParam, \
    ReactorRequestSampler #, ReactorSupplySampler
from cyclopts.execute import ArcFlow
        
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
        return samplers

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
        for name in s.__dict__:
            if hasattr(rc, name):
                vals = []
                args = CONSTR_ARGS[type(getattr(s, name))]
                attr = getattr(rc, name)
                for arg in args:
                    if arg in attr:
                        vals += [attr[arg]]
                if len(vals) > 0:
                    params_dict[name] = vals
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
    sim_id = t.StringCol(36) # len(str(uuid.uuid4())) == 36
    n_supply = t.Int32Col()
    n_request = t.Int32Col()
    n_sup_nodes = t.Int32Col()
    n_req_nodes = t.Int32Col()
    n_arcs = t.Int32Col()
    hash = t.Int64Col()

class RRSamplerDesc(t.IsDescription):
    sim_id = t.StringCol(36) # len(str(uuid.uuid4())) == 36
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
    time = t.Float64Col() # in seconds
    cyclus_version = t.StringCol(12)
    cyclopts_version = t.StringCol(12)

class Reporter(object):
    
    def report_solver(self, row, sim_id, sparams):
        row['sim_id'] = str(sim_id)
        row['type'] = sparams.type

    def report_graph(self, row, sim_id, gparams):
        row['sim_id'] = str(sim_id)
        row['n_supply'] = len(gparams.v_nodes_per_sup)
        row['n_request'] = len(gparams.u_nodes_per_req)
        row['n_sup_nodes'] = len(gparams.node_excl) - \
            len(gparams.def_constr_coeff)
        row['n_req_nodes'] = len(gparams.def_constr_coeff)
        row['n_arcs'] = len(gparams.arc_pref)
        row['hash'] = hash(gparams)
    
    def report_rr_sampler(self, row, sim_id, sampler):
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

        row['sim_id'] = str(sim_id)
        for param in params:
            if hasattr(s, param):
                row[param] = getattr(s, param).avg
        for param in bool_params:
            if hasattr(s, param):
                row[param] = getattr(s, param).cutoff
        for param in constr_params:
            if hasattr(s, param):
                row[param] = getattr(s, param).cutoff

    #
    # TO DO
    #
        
    # def report_rs_sampler(self, row, sim_id, sampler):
    #     row['sim_id'] = str(sim_id)
    
    def report_flows(self, row, sim_id, flows):
        for f in flows:
            row['sim_id'] = str(sim_id)
            row['arc_id'] = f.id
            row['flow'] = f.flow

    def report_solution(self, row, sim_id, soln):
        row['sim_id'] = str(sim_id)
        row['time'] = soln[0]
        row['cyclus_version'] = soln[1]
        row['cyclopts_version'] = soln[2]
            
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

    mode = "a" if os.path.exists(db_path) else "w"
    h5file = t.open_file(db_path, mode=mode, title="Cyclopts Output")
    
    flows = [ArcFlow(soln.flows[i:]) for i in range(len(soln.flows))]
    
    solnparams = [soln.time, soln.cyclus_version, cyclopts.__version__]

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
            h5file.create_table("/", name, desc, title)
        if hasattr(r, 'report_' + name):
            row = h5file.get_node('/' + name).row
            meth = getattr(r, 'report_' + name)
            meth(row, sim_id, data)
            row.append()
        
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
    