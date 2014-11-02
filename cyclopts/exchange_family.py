"""This module defines a ProblemFamily subclass for Cyclus Resource Exchanges.

:author: Matthew Gidden <matthew.gidden _at_ gmail.com>
"""
import numpy as np
from collections import Iterable

from cyclopts.problems import ProblemFamily
import cyclopts.cyclopts_io as cycio
import cyclopts.io_tools as io_tools
import cyclopts.tools as tools
import cyclopts.exchange_instance as exinst

_N_CAPS_MAX = 4

# add to this if more objects need to be persistable
_tbl_names = {
    "ExGroup": "ExchangeGroups",
    "ExNode": "ExchangeNodes",
    "properties": "ExchangeInstProperties",
    "solution_properties": "ExchangeInstSolutionProperties",    
    "pp": "PostProcess",
}

_grp_names = {
    "ExArc": "ExchangeArcs",
    "solutions": "ExchangeInstSolutions",    
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
        ("arc_id", np.int64),
        ("flow", np.float64),
        ]),
    "solution_properties": np.dtype([
        ("solnid", ('str', 16)), # 16 bytes for uuid
        ("instid", ('str', 16)), # 16 bytes for uuid
        ("pref_flow", np.float64),
        ("cyclus_version", ('str', 20)),
        ]),
    "pp": np.dtype([
        ("solnid", ('str', 16)), # 16 bytes for uuid
        ("pref_flow", np.float64),
        ]),
    }

def column_to_table(col):
    """return the table in which the column resides"""
    blacklist = ['paramid', 'instid', 'species', 'solnid']
    if col in blacklist:
        raise RuntimeError('Ambiguous column name.')
    tbl = None
    # hack for now
    if col == 'pref_flow':
        return _tbl_names["solution_properties"]
    for tbl, dt in _dtypes.items():
        if col in dt.fields.keys():
            tbl = _tbl_names[tbl]
            break
    return tbl

# these functions must be kept up to date with cyclopts.instance
def grp_tpl(instid, obj):    
    return(instid.bytes, 
           obj.id, 
           obj.kind, 
           np.append(obj.caps, [0] * (_N_CAPS_MAX - len(obj.caps))),
           np.append(obj.cap_dirs, [0] * (_N_CAPS_MAX - len(obj.cap_dirs))), 
           obj.qty,)

def node_tpl(instid, obj):    
    return(instid.bytes, obj.id, obj.gid, obj.kind, obj.qty, obj.excl, obj.excl_id)

def arc_tpl(obj):
    return(obj.id, 
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

def _iid_to_prefs(iid, tbl, narcs, strategy='col'):
    """return a numpy array of preferences"""
    if strategy == 'grp':
        return tbl.read(field='pref')
    # otherwise, do column strat
    ret = np.zeros(narcs)
    rows = cycio.uuid_rows(tbl, iid)
    ret[rows['id']] = rows['pref']
    # for x in rows:
    #     ret[x['id']] = x['pref']
    return ret
    
def _sid_to_flows(sid, tbl, narcs, strategy='col'):
    """return a numpy array of flows"""
    if strategy == 'col':
        ret = np.zeros(narcs)
        rows = cycio.uuid_rows(tbl, sid, colname='solnid')
        ret[rows['arc_id']] = rows['flow']
    elif strategy == 'grp':
        # conditional can be removed when all legacy dbs are converted
        if tbl.nrows == narcs:
            # fast
            return tbl.read(field='flow')
        else:
            ret = np.zeros(narcs)
            ret[tbl.read(field='arc_id')] = tbl.read(field='flow')
    # for x in rows:
    #     ret[x['arc_id']] = x['flow']
    return ret

def _pp_work_col(instid, solnids, prop_tbl, arc_tbl, soln_tbl):
    narcs = cycio.uuid_rows(prop_tbl, instid)[0]['n_arcs']
    prefs = _iid_to_prefs(instid, arc_tbl, narcs)
    sid_to_flows = {}
    data = []
    for sid in solnids:
        flows = _sid_to_flows(sid, soln_tbl, narcs)
        data.append((sid.bytes, np.dot(prefs, flows)))
        sid_to_flows[sid] = flows
    return narcs, sid_to_flows, data

def _pp_work_grp(instid, solnids, prop_tbl, arc_tbl, soln_tbl):
    narcs = cycio.uuid_rows(prop_tbl, instid)[0]['n_arcs']
    prefs = _iid_to_prefs(instid, arc_tbl, narcs, strategy='grp')
    sid_to_flows = {}
    data = []
    for sid in solnids:
        tbl = soln_tbl._f_get_child('id_' + sid.hex)
        flows = _sid_to_flows(sid, tbl, narcs, strategy='grp')
        data.append((sid.bytes, np.dot(prefs, flows)))
        sid_to_flows[sid] = flows
    return narcs, sid_to_flows, data

def _pp_work(instid, solnids, prop_tbl, arc_tbl, soln_tbl, strategy='col'):
    if strategy == 'col':
        return _pp_work_col(instid, solnids, prop_tbl, arc_tbl, soln_tbl)
    else:
        return _pp_work_grp(instid, solnids, prop_tbl, arc_tbl, soln_tbl)

class PathMap(io_tools.PathMap):
    """A simple container class for mapping columns to Hdf5 paths
    implemented for the ResourceExchange problem family"""
    
    def __init__(self, col):
        super(PathMap, self).__init__(col)
        
    @property
    def path(self):
        return '/'.join([ResourceExchange().io_prefix, 
                         column_to_table(self.col)])

class ResourceExchange(ProblemFamily):
    """A class representing families of resource exchange problems."""
    
    @property
    def name(cls):
        """
        Returns
        -------
        name : string
            The name of this species
        """
        return 'ResourceExchange'

    @property
    def property_table_name(cls):
        """
        Returns
        -------
        name : string
            The name of this family's instance property table
        """
        return _tbl_names['properties']
    
    @property
    def pp_table_name(cls):
        """
        Returns
        -------
        name : string
            The name of this family's instance postprocessing table
        """
        return _tbl_names['pp']
    
    def __init__(self):
        super(ResourceExchange, self).__init__()

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

    def register_groups(self, h5file, prefix):
        """Parameters
        ----------
        h5file : PyTables File
            the hdf5 file
        prefix : string
            the absolute path to the group for tables of this family

        Returns
        -------
        groups : list of cyclopts_io.Groups
            All groups that could be written to by this species.
        """
        return [cycio.Group(h5file, 
                            '/'.join([prefix, _grp_names[x]])) 
                for x in _grp_names.keys()]

    def record_inst(cls, inst, inst_uuid, param_uuid, species, io_manager=None):
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
        io_manager : cyclopts_io.IOManager, optional
            IOManager that gives access to tables/groups for writing
        """
        tables = None if io_manager is None else io_manager.tables
        h5groups = None if io_manager is None else io_manager.groups
        groups, nodes, arcs = inst
        
        data = [grp_tpl(inst_uuid, x) for x in groups]
        tables[_tbl_names['ExGroup']].append_data(data)
        
        data = [node_tpl(inst_uuid, x) for x in nodes]
        tables[_tbl_names['ExNode']].append_data(data)

        arc_grp = h5groups[_grp_names['ExArc']]
        arc_tbl_path = '/'.join([arc_grp.path, 
                                 'id_' + inst_uuid.hex])
        arc_tbl = cycio.Table(arc_grp.h5file, arc_tbl_path, _dtypes['ExArc'])
        io_manager.add_table(arc_tbl)
        data = [arc_tpl(x) for x in arcs]
        arc_tbl.append_data(data)

        data = [prop_tpl(inst_uuid, param_uuid, species, groups, nodes, arcs)]
        tables[_tbl_names['properties']].append_data(data)

    def record_soln(self, soln, soln_uuid, inst, inst_uuid, io_manager):
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
        io_manager : cyclopts_io.IOManager, optional
            IOManager that gives access to tables/groups for writing
        """
        tables = io_manager.tables
        h5groups = io_manager.groups
        groups, nodes, arcs = inst
        
        # full solution table
        soln_grp = h5groups[_grp_names['solutions']]
        soln_tbl_path = '/'.join([soln_grp.path, 
                                  'id_' + soln_uuid.hex])
        soln_tbl = cycio.Table(soln_grp.h5file, soln_tbl_path, 
                               _dtypes['solutions'])
        io_manager.add_table(soln_tbl)
        data = [(arcid, flow) for arcid, flow in soln.flows.items()]
        soln_tbl.append_data(data)
        
        # solution properties, 1 entry per soln
        tbl = tables[_tbl_names['solution_properties']]
        tbl.append_data([(soln_uuid.bytes, inst_uuid.bytes, soln.pref_flow, 
                          soln.cyclus_version)])
            
    def read_inst(self, uuid, io_manager):
        """Parameters
        ----------
        uuid : uuid
            The uuid of the instance to read
        io_manager : cyclopts_io.IOManager, optional
            IOManager that gives access to tables/groups for writing

        Returns
        -------
        inst : tuple of lists of ExGroups, ExNodes, and ExArgs
            A representation of a problem instance
        """
        ctors = {'ExGroup': exinst.ExGroup, 
                 'ExNode': exinst.ExNode}
        objs = {'ExGroup': [], 'ExNode': []}
        tables = io_manager.tables
        groups = io_manager.groups
        
        # this could be sped up by making groups and nodes their own simid tables
        for name in ctors.keys():
            tbl = tables[_tbl_names[name]]
            rows = tbl.uuid_rows(uuid)
            setattrs = tools.cyc_members(ctors[name]())
            for row in rows:
                obj = ctors[name]()
                if name == 'ExGroup':
                    ncaps = len([x for x in row['caps'] if x > 0])
                for var in setattrs:
                    attr = getattr(obj, var)
                    if isinstance(attr, Iterable):
                        ary = row[var]
                        if name == 'ExGroup':
                            attr = [ary[i] for i in range(ncaps)]
                        else:
                            attr = ary[ary > 0]
                    else:
                        attr = row[var]
                    #print('setting {0} to {1}'.format(var, attr))
                    setattr(obj, var, attr)
                objs[name].append(obj)
        
        grp = groups[_grp_names['ExArc']] 
        arcs = []
        # this could be sped up by directly populating members rather than 
        # dynamically typechecking each one 
        setattrs = tools.cyc_members(exinst.ExArc())
        for row in grp.group()._f_get_child('id_' + uuid.hex).read():
            obj = exinst.ExArc()
            for var in setattrs:
                attr = getattr(obj, var)
                if isinstance(attr, Iterable):
                    ary = row[var]
                    attr = ary[ary > 0]
                else:
                    attr = row[var]
                    #print('setting {0} to {1}'.format(var, attr))
                setattr(obj, var, attr)
            arcs.append(obj)
            
        return objs['ExGroup'], objs['ExNode'], arcs
            
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

    def post_process(self, instid, solnids, io_managers):
        """Perform any post processing on input and output.
        
        Parameters
        ----------
        instid : UUID 
            UUID of the instance to post process
        solnids : tuple of UUIDs
            a collection of solution UUIDs corresponding the instid 
        io_managers : tuple of cyclopts.cyclopts_io.IOManager
            iomanager from an input file, iomanager from an output file,
            and iomanager from a post-processed file

        Returns
        -------
        props : tuple 
            tuple of number of arcs and mapping of solution UUIDs to numpy 
            arrays of arc flows
        """
        intbls, outtbls, pptbls = (m.tables for m in io_managers)
        ingrps, outgrps, ppgrps = (m.groups for m in io_managers)
        prop_tbl = intbls[_tbl_names["properties"]]
        pp_tbl = pptbls[_tbl_names["pp"]]
        
        # determining column or group-based layout
        arc_io_name = _grp_names["ExArc"]
        soln_io_name = _grp_names["solutions"]
        if arc_io_name in intbls.keys():
            # column based layout
            arc_tbl = intbls[arc_io_name]
            soln_tbl = outtbls[soln_io_name]
            strategy = 'col'
        else:
            # group-based layout
            arc_tbl = ingrps[arc_io_name].group()._f_get_child('id_' + 
                                                               instid.hex)
            soln_tbl = outgrps[soln_io_name].group() # actually a group
            strategy = 'grp'
        
        narcs, sid_to_flows, data = _pp_work(instid, solnids, prop_tbl, 
                                             arc_tbl, soln_tbl, 
                                             strategy=strategy)
        pp_tbl.append_data(data)

        return narcs, sid_to_flows
