"""This module defines a ProblemFamily subclass for Cyclus Resource Exchanges.

:author: Matthew Gidden <matthew.gidden _at_ gmail.com>
"""
import numpy as np
from collections import Iterable

from cyclopts.problems import ProblemFamily
import cyclopts.cyclopts_io as cycio
import cyclopts.exchange_instance as exinst

_N_CAPS_MAX = 4

# add to this if more objects need to be persistable
_tbl_names = {
    "ExGroup": "ExchangeGroups",
    "ExNode": "ExchangeNodes",
    "ExArc": "ExchangeArcs",
    "properties": "ExchangeInstProperties",
    "solutions": "ExchangeInstSolutions",    
    "solution_properties": "ExchangeInstSolutionProperties",    
}

# this must be kept up to date with the cyclopts.instance classes
_dtypes = {
    "ExGroup": np.dtype([
        ("instid", ('str', 16)), # 16 bytes for uuid
        ("id", np.int64),
        ("kind", np.bool_),
        ("caps", (np.float64, _N_CAPS_MAX),), # array of size N_CAPS_MAX
        ("cap_dirs", (np.bool_, _N_CAPS_MAX),), # array of size N_CAPS_MAX
        ("qty", np.float64),
        ]),
    "ExNode": np.dtype([
        ("instid", ('str', 16)), # 16 bytes for uuid
        ("id", np.int64),
        ("gid", np.int64),
        ("kind", np.bool_),
        ("qty", np.float64),
        ("excl", np.bool_),
        ("excl_id", np.int64),
        ]),
    "ExArc": np.dtype([
        ("instid", ('str', 16)), # 16 bytes for uuid
        ("id", np.int64),
        ("uid", np.int64),
        ("ucaps", (np.float64, _N_CAPS_MAX),), # array of size N_CAPS_MAX
        ("vid", np.int64),
        ("vcaps", (np.float64, _N_CAPS_MAX),), # array of size N_CAPS_MAX
        ("pref", np.float64),
        ]),
    "properties": np.dtype([
        ("paramid", ('str', 16)), # 16 bytes for uuid
        ("instid", ('str', 16)), # 16 bytes for uuid
        ("species", ('str', 30)), # 30 is long enough..
        ("n_arcs", np.int64),
        ("n_u_grps", np.int64),
        ("n_v_grps", np.int64),
        ("n_u_nodes", np.int64),
        ("n_v_nodes", np.int64),
        ("n_constrs", np.int64),
        ("excl_frac", np.float64),
        ]),
    "solutions": np.dtype([
        ("solnid", ('str', 16)), # 16 bytes for uuid
        ("arc_id", np.int64),
        ("flow", np.float64),
        ]),
    "solution_properties": np.dtype([
        ("solnid", ('str', 16)), # 16 bytes for uuid
        ("instid", ('str', 16)), # 16 bytes for uuid
        ("pref_flow", np.float64),
        ("cyclus_version", ('str', 12)),
        ]),
    }

# these functions must be kept up to date with cyclopts.instance
def grp_tpl(instid, obj):    
    return(instid.bytes, obj.id, obj.kind, 
           np.append(obj.caps, [0] * (_N_CAPS_MAX - len(obj.caps))), obj.qty)

def node_tpl(instid, obj):    
    return(instid.bytes, obj.id, obj.gid, obj.kind, obj.qty, obj.excl, obj.excl_id)

def arc_tpl(instid, obj):
    return(instid.bytes, obj.id, 
           obj.uid, np.append(obj.ucaps, [0] * (_N_CAPS_MAX - len(obj.ucaps))), 
           obj.vid, np.append(obj.vcaps, [0] * (_N_CAPS_MAX - len(obj.vcaps))), 
           obj.pref)

def prop_tpl(instid, paramid, species, groups, nodes, arcs):
    nu_grps = sum(1 for g in groups if int(g.kind))
    nv_grps = len(groups) - nu_grps
    nu_nodes = sum(1 for n in nodes if n.kind)
    nv_nodes = len(nodes) - nu_nodes
    excl = {n.id: n.excl for n in nodes}
    excl_frac = sum(1.0 for a in arcs if excl[a.uid] or excl[a.vid]) / len(arcs)
    nconstr = sum(len(g.caps) for g in groups)
    return (paramid.bytes, instid.bytes, species, len(arcs), nu_grps, nv_grps, 
            nu_nodes, nv_nodes, nconstr, excl_frac)

class ResourceExchange(ProblemFamily):
    """A class representing families of resource exchange problems."""

    def __init__(self):
        super(ResourceExchange, self).__init__()

    @property
    def name(self):
        """
        Returns
        -------
        name : string
            The name of this species
        """
        return 'ResourceExchange'

    @property
    def property_table_name(self):
        """
        Returns
        -------
        name : string
            The name of this family's instance property table
        """
        return _tbl_names['properties']

    def register_tables(self, h5file, prefix):
        """Parameters
        ----------
        h5file : PyTables File
            the hdf5 file
        prefix : string
            the absolute path to the group for tables of this family

        Returns
        -------
        tables : list of cyclopts_io.Tables
            All tables that could be written to by this species.
        """
        return [cycio.Table(h5file, 
                            '/'.join([prefix, _tbl_names[x]]), 
                            _dtypes[x]) for x in _tbl_names.keys()]

    def record_inst(self, inst, inst_uuid, param_uuid, species, tables):
        """Parameters
        ----------
        inst : tuple of lists of ExGroups, ExNodes, and ExArgs
            A representation of a problem instance
        inst_uuid : uuid
            The uuid of the instance
        param_uuid : uuid
            The uuid of the point in parameter space
        species : str
            The name of the species that generated this instance
        tables : list of cyclopts_io.Table
            The tables that can be written to
        """
        groups, nodes, arcs = inst
        
        data = [grp_tpl(inst_uuid, x) for x in groups]
        tables[_tbl_names['ExGroup']].append_data(data)
        
        data = [node_tpl(inst_uuid, x) for x in nodes]
        tables[_tbl_names['ExNode']].append_data(data)
        
        data = [arc_tpl(inst_uuid, x) for x in arcs]
        tables[_tbl_names['ExArc']].append_data(data)
        
        data = [prop_tpl(inst_uuid, param_uuid, species, groups, nodes, arcs)]
        tables[_tbl_names['properties']].append_data(data)

    def record_soln(self, soln, soln_uuid, inst, inst_uuid, tables):
        """Parameters
        ----------
        soln : ExSolution
            A representation of a problem solution
        soln_uuid : uuid
            The uuid of the solution
        inst : tuple of lists of ExGroups, ExNodes, and ExArgs
            A representation of a problem instance
        inst_uuid : uuid
            The uuid of the instance
        tables : list of cyclopts_io.Table
            The tables that can be written to
        """
        groups, nodes, arcs = inst
        tbl = tables[_tbl_names['solutions']]
        for arcid, flow in soln.flows.iteritems():
            if flow > 0:
                tbl.append_data([(soln_uuid.bytes, arcid, flow)])
        tbl = tables[_tbl_names['solution_properties']]
        tbl.append_data([(soln_uuid.bytes, inst_uuid.bytes, soln.pref_flow, 
                          soln.cyclus_version)])
            
    def read_inst(self, uuid, tables):
        """Parameters
        ----------
        uuid : uuid
            The uuid of the instance to read
        tables : list of cyclopts_io.Table
            The tables that can be written to

        Returns
        -------
        inst : tuple of lists of ExGroups, ExNodes, and ExArgs
            A representation of a problem instance
        """
        xdattrs = lambda obj: [x for x in obj.__class__.__dict__.keys() \
                                   if not x.startswith('_')]
        ctors = {'ExGroup': exinst.ExGroup, 
                 'ExNode': exinst.ExNode, 
                 'ExArc': exinst.ExArc}
        objs = {'ExGroup': [], 'ExNode': [], 'ExArc': []}
        for name in ctors.keys():
            tbl = tables[_tbl_names[name]]
            rows = tbl.instid_rows(uuid.bytes)
            setattrs = xdattrs(ctors[name]())
            for row in rows:
                obj = ctors[name]()
                for var in setattrs:
                    attr = getattr(obj, var)
                    if isinstance(attr, Iterable):
                        ary = row[var]
                        attr = ary[ary > 0] 
                    else:
                        attr = row[var]
                    setattr(obj, var, attr)
                objs[name].append(obj)
        return objs['ExGroup'], objs['ExNode'], objs['ExArc']
            
    def run_inst(self, inst, solver, verbose=False):
        """Parameters
        ----------
        inst : tuple of lists of ExGroups, ExNodes, and ExArgs
            A representation of a problem instance
        solver : ProbSolver or similar
            A representation of a problem solver
        verbose : bool
            A verbosity flag

        Returns
        -------
        soln : ExSolution
            A representation of a problem solution
        """
        groups, nodes, arcs = inst
        soln = exinst.Run(groups, nodes, arcs, solver, verbose)
        return soln
