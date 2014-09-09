"""A module for defining structured request/supply species.

:author: Matthew Gidden <matthew.gidden _at_ gmail.com>
"""
import itertools
import numpy as np
import random
import math

from collections import OrderedDict, namedtuple, defaultdict, Iterable

from cyclopts import tools
from cyclopts import cyclopts_io as cycio
import cyclopts.exchange_instance as exinst
from cyclopts.problems import ProblemSpecies
from cyclopts.exchange_family import ResourceExchange

from cyclopts.structured_species import data as data

"""ordered mapping from input parameters to default values and np.dtypes, see
the theory manual for further explanation of the parameter names"""
Param = namedtuple('Param', ['val', 'dtype'])
parameters = {
    "f_rxtr": Param(0, np.int8),
    "f_fc": Param(0, np.int8),
    "f_loc": Param(0, np.int8),
    "n_rxtr": Param(0, np.uint32), # use a different tool for more than 4294967295 rxtrs! 
    "r_t_f": Param(1.0, np.float32),
    "r_th_pu": Param(0.0, np.float32), 
    "r_s_th": Param(1.0 / 2, np.float32),
    "r_s_mox_uox": Param(1.0, np.float32),
    "r_s_mox": Param(1.0 / 2, np.float32),
    "r_s_thox": Param(1.0 / 2, np.float32),
    "f_mox": Param(1.0, np.float32),
    "r_inv_proc": Param(1.0, np.float32), 
    "n_reg": Param(10, np.uint32), # use a different tool for more than 4294967295 regions! 
    "r_l_c": Param(1.0, np.float32),
    "seed": Param(-1.0, np.int64), # default is negative 
}
parameters = OrderedDict(sorted(parameters.items(), key=lambda t: t[0]))

def region(loc, n_reg=1):
    """assumes loc is on [0, 1]"""
    return int(math.floor(n_reg * loc))

def preference(base_pref, r_loc, s_loc, loc_fidelity=0, ratio=1., n_reg=1):
    """returns the preference between a requester and supplier for a commodity"""
    commod_pref = base_pref
    loc_pref = 0

    if loc_fidelity > 0: # at least coarse
        rreg = region(r_loc, n_reg=n_reg)
        sreg = region(s_loc, n_reg=n_reg)
        loc_pref = math.exp(-np.abs(rreg - sreg))
    
    if loc_fidelity > 1: # fine
        loc_pref = (loc_pref + math.exp(-np.abs(r_loc - s_loc))) / 2

    return commod_pref + ratio * loc_pref

class Point(object):
    """A container class representing a point in parameter space"""
    
    def __init__(self, d=None):
        """Parameters
        ----------
        d : dict, optional
            a dictionary with key value pairs of parameter name, parameter 
            value
        """
        d = d if d is not None else {}
        # init with dict-specified value else default
        for name, param in parameters.items():
            val = d[name] if name in d else param.val
            setattr(self, name, val)
        if self.seed > 0:
            random.seed(self.seed)

    def __eq__(self, other):
        return (isinstance(other, self.__class__) \
                    and self.__dict__ == other.__dict__)

    def __ne__(self, other):
        return not self.__eq__(other)

class Reactor(object):
    """A simplified reactor model for Structured Request Species"""
    
    def __init__(self, kind, point, gids, nids):
        self.kind = kind
        self.n_assems = 1 if point.f_rxtr == 0 else data.n_assemblies[kind]        

        self.nodes = []
        self.commod_to_nodes = defaultdict(list)
        self.enr_rnd = random.uniform(0, 1) 

        req = True
        qty = data.fuel_unit * data.request_qtys[self.kind]
        gid = gids.next()
        self.group = exinst.ExGroup(gid, req, [qty], qty)
        self.loc = data.loc()
        self.base_req_qty = qty / self.n_assems
        self._gen_nodes(point, gid, nids)

    def _gen_nodes(self, point, gid, nids):
        req = True
        excl = True
        for commod in data.rxtr_commods(self.kind, point.f_fc):
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

    def enr(self, commod):
        # node quantity takes into account relative fissile material
        lb, ub = data.enr_ranges[self.kind][commod]
        return (ub - lb) * self.enr_rnd + lb

    def req_qty(self, commod):
        return self.base_req_qty * data.relative_qtys[self.kind][commod]

    def coeffs(self, commod):
        return [1 / data.relative_qtys[self.kind][commod]]

class Supplier(object):
    """A simplified supplier model for Structured Request Species"""
    
    def __init__(self, kind, point, gids):
        self.kind = kind
        self.nodes = []

        req = True
        # process then inventory
        rhs = [data.sup_rhs[kind], 
               data.sup_rhs[kind] * point.r_inv_proc * data.conv_ratio(kind)]
        self.group = exinst.ExGroup(gids.next(), not req, rhs)
        self.loc = data.loc()

    def coeffs(self, qty, enr):
        return [data.converters[self.kind][k](
                qty, enr, data.sup_to_commod[self.kind]) / qty \
                    for k in ['proc', 'inv']]

class StructuredRequest(ProblemSpecies):
    """A class representing structured request-based exchanges species."""

    def __init__(self):
        super(StructuredRequest, self).__init__()
        self._family = ResourceExchange()
        self.space = None
        self._n_points = None
        # 16 bytes for uuid
        self.param_tbl_name = 'Points'
        self._param_dtype = np.dtype(
            [('paramid', ('str', 16)), ('family', ('str', 30))] + \
                [(name, param.dtype) for name, param in parameters.items()])
        self.sum_tbl_name = 'Summary'
        facs = ['n_r_th', 'n_r_f_mox', 'n_r_f_thox', 'n_s_uox', 'n_s_th_mox', 
                'n_s_f_mox', 'n_s_f_thox']
        self._sum_dtype = np.dtype(
            [('paramid', ('str', 16)), ('family', ('str', 30))] + \
                [(name, np.uint32) for name in facs])
            
        self.nids = tools.Incrementer()
        self.gids = tools.Incrementer()
        self.arcids = tools.Incrementer()

    @property
    def family(self):
        """Returns
        -------
        family : ResourceExchange
            An instance of this species' family
        """
        return self._family        

    @property
    def name(self):
        """Returns
        -------
        name : string
            The name of this species
        """
        return 'StructuredRequest'

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
                            self._sum_dtype)]

    def read_space(self, space_dict):
        """Parameters
        ----------
        space_dict : dict
            A dictionary container resulting from the reading in of a run 
            control file
        """
        self.space = {k: v if isinstance(v, Iterable) else [v] \
                          for k, v in space_dict.items() if k in parameters}

    @property
    def n_points(self):
        """Returns
        -------
        n : int
            The total number of points in the parameter space
        """
        if self._n_points is None: # lazy evaluation
            self._n_points = tools.n_permutations(self.space)
        return self._n_points
    
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
        for args in tools.expand_args(vals):
            d = {keys[i]: args[i] for i in range(len(args))}
            yield Point(d)    

    def record_point(self, point, param_uuid, tables):
        """Parameters
        ----------
        point : tuple or other
            A representation of a point in parameter space
        param_uuid : uuid
            The uuid of the point in parameter space
        tables : list of cyclopts_io.Table
            The tables that can be written to
        """
        uid = param_uuid.bytes if len(param_uuid.bytes) == 16 else param_uuid.bytes + '\0' 
        data = [param_uuid.bytes, self._family.name]
        data += [getattr(point, k) for k in parameters.keys()]
        tables[self.param_tbl_name].append_data([tuple(data)])
        data = [param_uuid.bytes, self._family.name]
        data += self._reactor_breakdown(point) + self._supplier_breakdown(point)
        tables[self.sum_tbl_name].append_data([tuple(data)])

    def _reactor_breakdown(self, point):
        """Returns
        -------
        n_uox, n_mox, n_thox : tuple
            the number of each reactor type
        """
        n_rxtr = point.n_rxtr
        fidelity = point.f_fc
        r_t_f = point.r_t_f # thermal to fast
        r_th_pu = point.r_th_pu # thox to mox
        n_uox, n_mox, n_thox = 0, 0, 0
        if fidelity == 0: # once through
            n_uox = max(n_rxtr, 1)
        elif fidelity == 1: # uox + fast mox
            n_uox = max(int(round(r_t_f * n_rxtr)), 1)
            n_mox = max(n_rxtr - n_uox, 1)
        else: # uox + fast mox + fast thox
            n_uox = max(int(round(r_t_f * n_rxtr)), 1)
            n_thox = max(int(round(r_th_pu * (n_rxtr - n_uox))), 1)
            n_mox = max(n_rxtr - n_uox - n_thox, 1)
        return n_uox, n_mox, n_thox

    def _get_reactors(self, point):
        n_uox, n_mox, n_thox = self._reactor_breakdown(point)
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

    def _supplier_breakdown(self, point):
        n_uox_r, n_mox_r, n_thox_r = self._reactor_breakdown(point)
        n_uox, n_t_mox, n_f_mox, n_f_thox = 0, 0, 0, 0
        fidelity = point.f_fc

        # number thermal suppliers
        if fidelity == 0: # once through - only uox
            n_uox = max(int(round(point.r_s_th * n_uox_r)), 1)
        else:
            n_s_t = max(int(round(point.r_s_th * n_uox_r)), 1)
            n_uox = max(int(round(n_s_t / (1.0 + point.r_s_mox_uox))), 1)
            n_t_mox = max(n_s_t - n_uox, 1)

        # number f_mox suppliers
        if fidelity > 0:
            n_f_mox = max(int(round(point.r_s_mox * n_mox_r)), 1)
            
        # number f_thox suppliers
        if fidelity > 1:
            n_f_thox = max(int(round(point.r_s_thox * n_thox_r)), 1)
 
        return n_uox, n_t_mox, n_f_mox, n_f_thox

    def _get_suppliers(self, point):
        n_uox, n_t_mox, n_f_mox, n_f_thox = self._supplier_breakdown(point)
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
        pref = preference(data.rxtr_pref_basis[r.kind][commod], r.loc, s.loc, 
                          point.f_loc, point.r_l_c, point.n_reg)
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
                for commod in data.rxtr_commods(r.kind, point.f_fc):
                    for s in suppliers[data.commod_to_sup[commod]]:
                        supply = self._generate_supply(point, commod, r, s)
                        arcs.append(supply)
        return np.concatenate(arcs)          

    def gen_inst(self, point):
        """Parameters
        ----------
        point :  structured_species.Point
            A representation of a point in parameter space
           
        Returns
        -------
        inst : tuple of lists of ExGroups, ExNodes, and ExArgs
            A representation of a problem instance to be used by this species' 
            family
        """            
        # reset id generation
        self.nids = tools.Incrementer()
        self.gids = tools.Incrementer()
        self.arcids = tools.Incrementer()

        # species objects
        reactors = self._get_reactors(point)        
        suppliers = self._get_suppliers(point)        

        # create arcs
        arcs = self._get_arcs(point, reactors, suppliers)
        
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