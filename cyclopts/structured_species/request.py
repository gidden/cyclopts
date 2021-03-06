"""A module for defining structured request species.

:author: Matthew Gidden <matthew.gidden _at_ gmail.com>
"""
import itertools
import numpy as np
import random
import math

from collections import OrderedDict, defaultdict, Iterable

from cyclopts import tools as cyctools
from cyclopts import cyclopts_io as cycio
from cyclopts import io_tools as io_tools
import cyclopts.exchange_instance as exinst
from cyclopts.problems import ProblemSpecies
from cyclopts.exchange_family import ResourceExchange

from cyclopts.structured_species import data
from cyclopts.structured_species import tools as strtools

def rxtr_commods(kind, fidelity):
    """return a list of commodities per reactor kind and fidelity"""
    commods = [data.Commodities.uox]
    if fidelity > 0:
        commods += [data.Commodities.th_mox, data.Commodities.f_mox]
    if fidelity > 1 and kind != data.Reactors.th:
        commods += [data.Commodities.f_thox]
    return commods

class Point(strtools.Point):
    """A container class representing a point in parameter space"""

    """ordered mapping from input parameters to default values and np.dtypes, see
    the theory manual for further explanation of the parameter names"""
    parameters = OrderedDict(sorted({
        "f_rxtr": strtools.Param(0, np.int8),
        "f_fc": strtools.Param(0, np.int8),
        "f_loc": strtools.Param(0, np.int8),
        # use a different tool for more than 4294967295 rxtrs! 
        "n_rxtr": strtools.Param(1, np.uint32), 
        "r_t_f": strtools.Param(1.0, np.float32),
        "r_th_pu": strtools.Param(0.0, np.float32), 
        "r_s_th": strtools.Param(1.0 / 2, np.float32),
        "r_s_mox_uox": strtools.Param(1.0, np.float32),
        "r_s_mox": strtools.Param(1.0 / 2, np.float32),
        "r_s_thox": strtools.Param(1.0 / 2, np.float32),
        "f_mox": strtools.Param(1.0, np.float32),
        "r_inv_proc": strtools.Param(1.0, np.float32), 
        # use a different tool for more than 4294967295 regions! 
        "n_reg": strtools.Param(10, np.uint32), 
        "r_l_c": strtools.Param(1.0, np.float32),
        "seed": strtools.Param(-1.0, np.int64), # default is negative 
        }.items(), key=lambda t: t[0]))
    
    def __init__(self, d=None):
        """Parameters
        ----------
        d : dict, optional
            a dictionary with key value pairs of parameter name, parameter 
            value
        """
        super(Point, self).__init__(d)
        if self.seed > 0:
            random.seed(self.seed)

    def _parameters(self):
        return Point.parameters

class Reactor(strtools.Reactor):
    """An extension reactor model for Structured Request Species"""
    
    def __init__(self, kind, point, gids, nids):
        super(Reactor, self).__init__(kind, point)
        req = True
        qty = data.fuel_unit * data.core_vol_frac[self.kind]
        self.base_req_qty = qty / self.n_assems
        gid = gids.next()
        grp = exinst.ExGroup(gid, req, qty)
        grp.AddCap(qty)
        self.group = grp
        self._gen_nodes(point, gid, nids)

    def _gen_nodes(self, point, gid, nids):
        self.nodes = []
        self.commod_to_nodes = defaultdict(list)
        req = True
        excl = True
        for commod in rxtr_commods(self.kind, point.f_fc):
            nreq = self.n_assems
            # account for less mox requests
            if self.kind == data.Reactors.th:
                if commod == data.Commodities.f_mox or \
                        commod == data.Commodities.th_mox:
                    nreq = int(math.ceil(nreq * point.f_mox))
            for i in range(nreq):
                node = exinst.ExNode(nids.next(), gid, req, 
                                     self.req_qty(commod), excl)
                self.nodes.append(node)
                self.commod_to_nodes[commod].append(node)

    def req_qty(self, commod):
        return self.base_req_qty * data.relative_qtys[self.kind][commod]

class Supplier(object):
    """A simplified supplier model for Structured Request Species"""
    
    def __init__(self, kind, point, gids):
        self.kind = kind
        self.nodes = []

        req = True
        # process then inventory
        rhs = [data.sup_rhs[kind], 
               data.sup_rhs[kind] * point.r_inv_proc * strtools.conv_ratio(kind)]
        grp = exinst.ExGroup(gids.next(), not req)
        for cap in rhs:
            grp.AddCap(cap)
        self.group = grp
        self.loc = data.loc()

    def coeffs(self, qty, enr):
        return [data.converters[self.kind][k](
                qty, enr, data.sup_to_commod[self.kind]) / qty \
                    for k in ['proc', 'inv']]

class PathMap(io_tools.PathMap):
    """A simple container class for mapping columns to Hdf5 paths
    implemented for the StructuredRequest problem species"""
    
    def __init__(self, col):
        super(PathMap, self).__init__(col)
        
    @property
    def path(self):
        # this is an approx. heuristic, it might need to be updated
        inst = StructuredRequest()
        col = self.col
        if col.startswith('n_') and not col.endswith('_rxtr') \
                and not col.endswith('_reg'):
            tbl = inst.sum_tbl_name
        elif col.endswith('pref_flow') or col.endswith('cost_flow'):
            tbl = strtools.pp_tbl_name
        else:
            tbl = inst.param_tbl_name
        return '/'.join([inst.io_prefix, tbl])

class StructuredRequest(ProblemSpecies):
    """A class representing structured request-based exchanges species."""

    @property
    def family(cls):
        """Returns
        -------
        family : ResourceExchange
            An instance of this species' family
        """
        return ResourceExchange()        

    @property
    def name(cls):
        """Returns
        -------
        name : string
            The name of this species
        """
        return 'StructuredRequest'

    @property
    def param_tbl_name(cls):
        """Returns
        -------
        name : string
            The name of parameter space output table
        """
        return 'Points'

    @property
    def sum_tbl_name(cls):
        """Returns
        -------
        name : string
            The name of summary output table
        """
        return 'Summary'

    @property
    def summary_tbls(cls):
        """
        Returns
        -------
        name : list
            A list of cyclopts_io.TblDesc for summary tables.
        """
        return strtools.tbl_descs(cls.io_prefix) + [
            cycio.TblDesc('/'.join([cls.io_prefix, cls.sum_tbl_name]), 
                          'param', 'paramid'),
            cycio.TblDesc('/'.join([cls.io_prefix, cls.param_tbl_name]), 
                          'param', 'paramid'),
            ]
    
    def __init__(self):
        super(StructuredRequest, self).__init__()
        self.space = None
        self._n_points = None
        # 16 bytes for uuid
        self._param_dtype = np.dtype(
            [('paramid', ('str', 16)), ('family', ('str', 30))] + \
                [(name, param.dtype) for name, param in Point.parameters.items()])
        facs = ['n_r_th', 'n_r_f_mox', 'n_r_f_thox', 'n_s_uox', 'n_s_th_mox', 
                'n_s_f_mox', 'n_s_f_thox']
        self._sum_dtype = np.dtype(
            [('paramid', ('str', 16)), ('family', ('str', 30))] + \
                [(name, np.uint32) for name in facs])
            
        self.nids = cyctools.Incrementer()
        self.gids = cyctools.Incrementer()
        self.arcids = cyctools.Incrementer()
        self.instid = None
        self.tables = None
        self.groups = None
        self.arc_tbl = None
        
    def register_tables(self, h5file, prefix):
        """Parameters
        ----------
        h5file : PyTables File
            the hdf5 file
        prefix : string
            the absolute path to the group for tables of this species

        Returns
        -------
        tables : list of cyclopts_io.Tables
            All tables that could be written to by this species.
        """
        return [cycio.Table(h5file, '/'.join([prefix, self.param_tbl_name]), 
                            self._param_dtype),
                cycio.Table(h5file, '/'.join([prefix, self.sum_tbl_name]), 
                            self._sum_dtype),
                cycio.Table(h5file, '/'.join([prefix, strtools.pp_tbl_name]), 
                            strtools.pp_tbl_dtype),]

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
        return [cycio.Group(h5file, '/'.join([prefix, strtools.arc_io_name]))]

    def read_space(self, space_dict):
        """Parameters
        ----------
        space_dict : dict
            A dictionary container resulting from the reading in of a run 
            control file
        """
        self.space = {k: v if isinstance(v, Iterable) else [v] \
                          for k, v in space_dict.items() \
                          if k in Point.parameters}

    @property
    def n_points(self):
        """Returns
        -------
        n : int
            The total number of points in the parameter space
        """
        return cyctools.n_permutations(self.space)
    
    def points(self):
        """Derived classes must implement this function returning a
        representation of a point in its parameter space to be used by other
        class member functions.
        
        Returns
        -------
        point_generator : generator
            A generator for representation of a point in parameter space to be 
            used by this species
        """
        keys = self.space.keys()
        vals = self.space.values()
        for args in cyctools.expand_args(vals):
            d = {keys[i]: args[i] for i in range(len(args))}
            yield Point(d)    

    def record_point(self, point, param_uuid, io_manager):
        """Parameters
        ----------
        point : tuple or other
            A representation of a point in parameter space
        param_uuid : uuid
            The uuid of the point in parameter space
        io_manager : cyclopts_io.IOManager, optional
            IOManager that gives access to tables/groups for writing
        """
        tables = io_manager.tables
        uid = param_uuid.bytes if len(param_uuid.bytes) == 16 \
            else param_uuid.bytes + '\0' 
        
        data = [param_uuid.bytes, self.family.name]
        data += [getattr(point, k) for k in Point.parameters.keys()]
        tables[self.param_tbl_name].append_data([tuple(data)])
        
        data = [param_uuid.bytes, self.family.name]
        data += strtools.reactor_breakdown(point)
        data += strtools.support_breakdown(point)[:-1]
        tables[self.sum_tbl_name].append_data([tuple(data)])

    def _get_reactors(self, point):
        n_uox, n_mox, n_thox = strtools.reactor_breakdown(point)
        uox_th_r = np.ndarray(
            shape=(n_uox,), 
            buffer=np.array([Reactor(data.Reactors.th, point, 
                                     self.gids, self.nids) \
                                 for i in range(n_uox)]), 
            dtype=Reactor)
        mox_f_r = np.ndarray(
            shape=(n_mox,), 
            buffer=np.array([Reactor(data.Reactors.f_mox, point, 
                                     self.gids, self.nids) \
                                 for i in range(n_mox)]), 
            dtype=Reactor)
        thox_f_r = np.ndarray(
            shape=(n_thox,), 
            buffer=np.array([Reactor(data.Reactors.f_thox, point, 
                                     self.gids, self.nids) \
                                 for i in range(n_thox)]), 
            dtype=Reactor)
        reactors = {
            data.Reactors.th: uox_th_r,
            data.Reactors.f_mox: mox_f_r,
            data.Reactors.f_thox: thox_f_r,
            }
        return reactors

    def _get_suppliers(self, point):
        n_uox, n_t_mox, n_f_mox, n_f_thox, _ = strtools.support_breakdown(point)
        uox_s = np.ndarray(
            shape=(n_uox,), 
            buffer=np.array([Supplier(data.Supports.uox, point, self.gids) \
                                 for i in range(n_uox)]), 
            dtype=Supplier)
        mox_th_s = np.ndarray(
            shape=(n_t_mox,), 
            buffer=np.array([Supplier(data.Supports.th_mox, point, self.gids) \
                                 for i in range(n_t_mox)]), 
            dtype=Supplier)
        mox_f_s = np.ndarray(
            shape=(n_f_mox,), 
            buffer=np.array([Supplier(data.Supports.f_mox, point, self.gids) \
                                 for i in range(n_f_mox)]), 
            dtype=Supplier)
        thox_s = np.ndarray(
            shape=(n_f_thox,), 
            buffer=np.array([Supplier(data.Supports.f_thox, point, self.gids) \
                                 for i in range(n_f_thox)]), 
            dtype=Supplier)
        suppliers = {
            data.Supports.uox: uox_s,
            data.Supports.th_mox: mox_th_s,
            data.Supports.f_mox: mox_f_s,
            data.Supports.f_thox: thox_s,
            }
        return suppliers

    def _generate_supply(self, point, commod, requester, supplier):
        r = requester
        s = supplier
        commod_pref = data.rxtr_pref_basis[r.kind][commod]
        loc_pref = strtools.loc_pref(r.loc, s.loc, point.f_loc, point.n_reg)
        pref = commod_pref + loc_pref * point.r_l_c
        rnodes = r.commod_to_nodes[commod]
        arcs = []
        enr = r.enr(commod)

        # req coeffs have full orders take into relative fissile material
        req_coeffs = r.coeffs(commod)

        # sup coeffs act on the quantity of fissile material 
        qty = r.req_qty(commod)
        sup_coeffs = s.coeffs(qty, enr)
        for i in range(len(rnodes)):
            req = True
            nid = self.nids.next()
            node = exinst.ExNode(nid, s.group.id, not req, qty)
            s.nodes.append(node)
            arcid = self.arcids.next()
            if self.arc_tbl is not None:
                self.arc_tbl.append_data([(arcid, commod, commod_pref, loc_pref)])
            #print('id', arcid, 'commod', commod, 'pref', pref)
            arcs.append(exinst.ExArc(
                    arcid,
                    rnodes[i].id, req_coeffs,
                    nid, sup_coeffs,
                    pref))
        return arcs

    def _get_arcs(self, point, reactors, suppliers):
        arcs = []
        for r_kind, r_ary in reactors.items():
            for r in r_ary:
                for commod in rxtr_commods(r.kind, point.f_fc):
                    for s in suppliers[data.commod_to_sup[commod]]:
                        supply = self._generate_supply(point, commod, r, s)
                        arcs.append(supply)
        return np.concatenate(arcs)          

    def gen_inst(self, point, instid=None, io_manager=None):
        """Parameters
        ----------
        point :  structured_species.Point
            A representation of a point in parameter space
        instid : uuid
            the id for the instance
        io_manager : cyclopts_io.IOManager, optional
            IOManager that gives access to tables/groups for writing
           
        Returns
        -------
        inst : tuple of lists of ExGroups, ExNodes, and ExArgs
            A representation of a problem instance to be used by this species' 
            family
        """      
        # reset id generation
        self.nids = cyctools.Incrementer()
        self.gids = cyctools.Incrementer()
        self.arcids = cyctools.Incrementer()
        self.instid = instid
        
        # set up IO
        self.tables = None if io_manager is None else io_manager.tables
        self.groups = None if io_manager is None else io_manager.groups
        self.arc_tbl = None
        if self.groups is not None:
            arc_grp = self.groups[strtools.arc_io_name]
            arc_tbl_path = '/'.join([arc_grp.path, 
                                     'id_' + self.instid.hex])
            self.arc_tbl = cycio.Table(arc_grp.h5file, arc_tbl_path, strtools.arc_tbl_dtype)
            self.arc_tbl.cond_create()

        # species objects
        reactors = self._get_reactors(point)        
        suppliers = self._get_suppliers(point)        

        # create arcs
        arcs = self._get_arcs(point, reactors, suppliers)
        if self.arc_tbl is not None:
            self.arc_tbl.flush()
        
        # collect nodes
        r_nodes = np.concatenate([x.nodes for ary in reactors.values() \
                                     for x in ary])
        s_nodes = np.concatenate([x.nodes for ary in suppliers.values() \
                                     for x in ary])
        nodes = np.concatenate((r_nodes, s_nodes))

        # collect groups
        r_groups = [x.group for ary in reactors.values() for x in ary]
        s_groups = [x.group for ary in suppliers.values() for x in ary]
        groups = np.concatenate((r_groups, s_groups))

        return groups, nodes, arcs

    def post_process(self, instid, solnids, props, io_managers):
        """Perform any post processing on input and output.
        
        Parameters
        ----------
        instid : UUID 
            UUID of the instance to post process
        solnids : tuple of UUIDs
            a collection of solution UUIDs corresponding the instid 
        props : tuple, other
            as defined by cyclopts.exchange_family 
        io_managers : tuple of cyclopts.cyclopts_io.IOManager
            iomanager from an input file, iomanager from an output file,
            and iomanager from a post-processed file
        """
        strtools.post_process(instid, solnids, props, io_managers, self.name)
