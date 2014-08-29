"""A module for defining structured request/supply species.

:author: Matthew Gidden <matthew.gidden _at_ gmail.com>
"""
import itertools
import numpy as np
import random

from collections import OrderedDict, namedtuple, defaultdict

from cyclopts import tools
from cyclopts import cyclopts_io as cycio
import cyclopts.exchange_instance as exinst
from cyclopts.problems import ProblemSpecies
from cyclopts.exchange_family import ResourceExchange
from cyclopts import structured_species_data as data

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
    "f_mox": Param(1.0 / 3, np.float32),
    "r_inv_proc": Param(1.0, np.float32), 
    "n_reg": Param(10, np.uint32), # use a different tool for more than 4294967295 regions! 
    "r_l_c": Param(1.0, np.float32),
    "seed": Param(-1.0, np.int64), # default is negative 
}
parameters = OrderedDict(sorted(parameters.items(), key=lambda t: t[0]))

def region(point, loc):
    """assumes loc is on [0, 1]"""
    nreg = point.n_reg
    return int(math.floor(nreg * loc))

def preference(point, commod, requester, supplier):
    """returns the preference between a requester and supplier for a commodity"""
    commod_pref = data.pref_basis[requester.kind][commod]
    loc_pref = 0

    if point.f_loc > 0: # at least coarse
        rloc = requester.loc
        sloc = supplier.loc
        rreg = region(point, rloc)
        sreg = region(point, sloc)
        loc_pref = math.exp(-np.abs(rreg - sreg))
    
    if point.f_loc > 1: # fine
        loc_pref = (loc_pref + math.exp(-np.abs(rloc - sloc))) / 2

    return commod_pref + point.r_l_c * loc_pref

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
        self.n_assems = n = 1 if point.f_rxtr == 0 else data.n_assemblies[kind]        

        self.nodes = []
        self.commod_to_nodes = defaultdict(list)
        self.enr = {}

        req = True
        excl = True
        qty = data.fuel_unit * data.request_qtys[kind]
        self.req_qty = qty / n
        gid = gids.next()
        for commod in data.rxtr_commods(kind, point.f_fc):
            req_qty = self.req_qty * data.relative_qtys[kind][commod]
            lb, ub = data.enr_ranges[kind][commod]
            self.enr[commod] = random.uniform(lb, ub) # one enr per commod per reactor
            for i in range(n):
                node = exinst.ExNode(nids.next(), gid, req, req_qty, excl)
                self.nodes.append(node)
                self.commod_to_nodes[commod].append(node)

        self.group = exinst.ExGroup(gid, req, [qty], qty)
        self.loc = data.loc()

class Supplier(object):
    """A simplified supplier model for Structured Request Species"""
    
    def __init__(self, kind, point, gids):
        self.kind = kind
        self.nodes = None

        req = True
        # process then inventory
        rhs = [data.sup_rhs[kind], 
               data.sup_rhs[kind] * point.r_inv_proc * data.conv_ratio(kind)]
        self.group = exinst.ExGroup(gids.next(), not req, rhs)
        self.loc = data.loc()

class StructuredRequest(ProblemSpecies):
    """A class representing structured request-based exchanges species."""

    def __init__(self):
        super(StructuredRequest, self).__init__()
        self.tbl_name = 'StructuredRequestParameters'
        self._family = ResourceExchange()
        self.space = None
        self._n_points = None
        # 16 bytes for uuid
        self._dtype = np.dtype(
            [('paramid', ('str', 16)), ('family', ('str', 30))] + \
                [(name, param.dtype) for name, param in parameters.items()])
    
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
        return [cycio.Table(h5file, '/'.join([prefix, self.tbl_name]), 
                            self._dtype)]

    def read_space(self, space_dict):
        """Parameters
        ----------
        space_dict : dict
            A dictionary container resulting from the reading in of a run 
            control file
        """
        self.space = {k: v for k, v in space_dict.items() if k in parameters}

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
        for tup in itertools.product(vals):
            d = {keys[i]: tup[i] for i in range(len(tup))}
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
        for k in parameters.keys():
            print(k)
        data = [param_uuid.bytes, self._family.name]
        data += [getattr(point, k) for k in parameters.keys()]
        tables[self.tbl_name].append_data(tuple(data))

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
            n_uox = n_rxtr
        elif fidelity == 1: # uox + fast mox
            n_uox = int(round(r_t_f * n_rxtr))
            n_mox = n_rxtr - n_uox
        else: # uox + fast mox + fast thox
            n_uox = int(round(r_t_f * n_rxtr))
            n_thox = int(round(r_th_pu * (n_rxtr - n_uox)))
            n_mox = n_rxtr - n_uox - n_thox
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
            n_uox = int(round(point.r_s_th * n_uox_r))
        else:
            n_s_t = int(round(point.r_s_th * n_uox_r)) 
            n_uox = int(round(n_s_t / (1.0 + point.r_s_mox_uox)))
            n_t_mox = n_s_t - n_uox

        # number f_mox suppliers
        if fidelity > 0:
            n_f_mox = int(round(point.r_s_mox * n_mox_r))
            
        # number f_thox suppliers
        if fidelity > 1:
            n_f_thox = int(round(point.r_s_thox * n_thox_r))
 
        return n_uox, n_t_mox, n_f_mox, n_f_thox

    def _get_suppliers(self, point):
        n_uox, n_t_mox, n_f_mox, n_f_thox = self._supplier_breakdown(point)
        print(n_uox, n_t_mox, n_f_mox, n_f_thox)
        uox_s = np.ndarray(
            shape=(n_uox,), 
            buffer=np.array([Supplier(data.Suppliers.uox, point, self.gids) \
                                 for i in range(n_uox)]), 
            dtype=Supplier)
        mox_th_s = np.ndarray(
            shape=(n_t_mox,), 
            buffer=np.array([Supplier(data.Suppliers.th_mox, point, self.gids) \
                                 for i in range(n_t_mox)]), 
            dtype=Supplier)
        mox_f_s = np.ndarray(
            shape=(n_f_mox,), 
            buffer=np.array([Supplier(data.Suppliers.f_mox, point, self.gids) \
                                 for i in range(n_f_mox)]), 
            dtype=Supplier)
        thox_s = np.ndarray(
            shape=(n_f_thox,), 
            buffer=np.array([Supplier(data.Suppliers.f_thox, point, self.gids) \
                                 for i in range(n_f_thox)]), 
            dtype=Supplier)
        suppliers = {
            data.Suppliers.uox: uox_s,
            data.Suppliers.th_mox: mox_th_s,
            data.Suppliers.f_mox: mox_f_s,
            data.Suppliers.f_thox: thox_s,
            }
        return suppliers

    def _generate_supply(self, point, commod, requester, supplier):
        r = requester
        s = supplier
        pref = preference(point, commod, r, s)
        rnodes = r.commod_to_nodes[commod]
        arcs = []
        enr = requester.enr[commod]
        req_coeffs = [r.req_qty / data.relative_qtys[r.kind][commod]]
        converters = data.converter[kind]
        sup_coeffs = [c[k](r.req_qty * data.relative_qtys[r.kind][commod], 
                           enr, commod) for k in ['proc', 'inv']]
        for i in range(len(rnodes)):
            req = True
            nid = self.nids.next()
            node = exinst.ExNode(nid, s.group.id, not req)
            s.nodes.append(node)
            arcs.append(exinst.ExArc(
                    self.arcids.next(),
                    rnodes[i].id, req_coeffs,
                    nid, sup_coeffs,
                    pref))
        return arcs

    def _get_arcs(self, point, reactors, suppliers):
        arcs = []
        for r_kind, r_ary in reactors.items():
            for r in r_ary:
                for commod in data.rxtr_commods(r.kind, point.f_fc):
                    for s_ary in suppliers[data.commod_to_sup[commod]]:
                        print(s_ary)
                        for s in s_ary:
                            arcs.append(
                                self._generate_supply(point, commod, r, s))
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
        r_groups = [x.group for ary in suppliers.values() for x in ary]
        groups = np.concatenate((r_groups, s_groups))

        return groups, nodes, arcs
