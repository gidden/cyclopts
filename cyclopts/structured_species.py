"""A module for defining structured request/supply species.

:author: Matthew Gidden <matthew.gidden _at_ gmail.com>
"""
import numpy as np

from collections import OrderedDict, namedtuple

from cyclopts.problems import ProblemSpecies
from cyclopts import structured_species_data as data

"""ordered mapping from input parameters to default values and np.dtypes, see
the theory manual for further explanation of the parameter names"""
Param = namedtuple('Param', ['val', 'dtype'])
parameters = {
    "f_rxtr": Param(0, np.int8),
    "f_fc": Param(0, np.int8),
    "f_loc": Param(0, np.int8),
    "n_rxtr": Param(0, np.uint32), # use a different tool for more than 4294967295 rxtrs! 
    "r_t_f": Param(1, np.float32),
    "r_th_pu": Param(0, np.float32), 
    "r_s_r": Param(0.5, np.float32),
    "f_mox": Param(1.0/3, np.float32),
    "r_inv_proc": Param(1.0, np.float32), 
    "n_reg": Param(0, np.uint32), # use a different tool for more than 4294967295 regions! 
    "r_l_c": Param(1.0, np.float32),
}
parameters = OrderedDict(sorted(parameters.items(), key=lambda t: t[0]))

# class Point(RunControl):
#     """A container class representing a point in parameter space"""
    
#     def __init__()

class Reactor(object):
    """A simplified reactor model for Structured Request Species"""
    
    def __init__(self, kind, point):
        # this init function should set up structured species members and generate ExNodes
        self.kind = kind
        self.n_assems = None
        self.nodes = None
        self.commod_to_nodes = None
        self.group = None
        self.loc = None

class Supplier(object):
    """A simplified reactor model for Structured Request Species"""
    
    def __init__(self, kind, point):
        # this init function should set up structured species members 
        # it should *not* generate ExNodes
        self.kind = kind
        self.converters = None
        self.rhs = None
        self.nodes = None
        self.group = None
        self.loc = None

class StructuredRequest(ProblemSpecies):
    """A class representing structured request-based exchanges species."""

    def __init__(self):
        super(StructuredRequest, self).__init__()
        self.tbl_name = 'StructuredRequestParameters'
        self.space = None
        self._n_points = None

    @property
    def family(self):
        """Returns
        -------
        family : ResourceExchange
            An instance of this species' family
        """
        return ResourceExchange()        

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
        dtype = np.dtype([(k, v[1]) for k, v in parameters.items()])
        return [cycio.Table(h5file, '/'.join([prefix, self.tbl_name]), dtype)]

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
        if self._n_points is None:
            pass
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
        raise NotImplementedError    

    def record_point(self, point, param_uuid, tables):
        """Derived classes must implement this function, recording information
        about a parameter point in the appropriate tables.
        
        Parameters
        ----------
        point : tuple or other
            A representation of a point in parameter space
        param_uuid : uuid
            The uuid of the point in parameter space
        tables : list of cyclopts_io.Table
            The tables that can be written to
        """
        raise NotImplementedError

    def _reactor_breakdown(self, point):
        pass

    def _get_reactors(self, point):
        n_uox, n_mox, n_thox = self._reactor_breakdown(point)
        uox_th_r = np.ndarray(
            shape=(n_uox,), 
            buffer=np.array([Reactor(data.Reactors.th, point) \
                                 for i in range(n_uox)]), 
            dtype=Reactor)
        mox_f_r = np.ndarray(
            shape=(n_mox,), 
            buffer=np.array([Reactor(data.Reactors.f_mox, point) \
                                 for i in range(n_uox)]), 
            dtype=Reactor)
        thox_f_r = np.ndarray(
            shape=(n_thox,), 
            buffer=np.array([Reactor(data.Reactors.f_thox, point) \
                                 for i in range(n_uox)]), 
            dtype=Reactor)
        reactors = {
            data.Reactors.th: uox_th_r,
            data.Reactors.f_mox: mox_th_r,
            data.Reactors.f_thox: thox_f_r,
            }
        return reactors

    def _supplier_breakdown(self, point):
        pass

    def _get_suppliers(self, point):
        n_uox, n_t_mox, n_f_mox, n_thox = self._supplier_breakdown(point)
        uox_s = np.ndarray(
            shape=(n_uox), 
            buffer=np.array([Supplier(data.Suppliers.uox, point) \
                                 for i in range(n_uox)]), 
            dtype=Supplier)
        mox_th_s = np.ndarray(
            shape=(n_mox), 
            buffer=np.array([Supplier(data.Suppliers.th_mox, point) \
                                 for i in range(n_uox)]), 
            dtype=Supplier)
        mox_f_s = np.ndarray(
            shape=(n_mox), 
            buffer=np.array([Supplier(data.Suppliers.f_mox, point) \
                                 for i in range(n_uox)]), 
            dtype=Supplier)
        thox_s = np.ndarray(
            shape=(n_thox), 
            buffer=np.array([Supplier(data.Suppliers.f_thox, point) \
                                 for i in range(n_uox)]), 
            dtype=Supplier)
        suppliers = {
            Suppliers.uox: uox_s,
            Suppliers.th_mox: mox_t_s,
            Suppliers.f_mox: mox_f_s,
            Suppliers.f_thox: thox_s,
            }
        return suppliers

    def _generate_supply(self, point, r_kind, commod, r_nodes, s_kind, supplier):
        # this function should generate the supply for a single reactor from a single supplier
        # supplier nodes should be added
        # arcs should be generated and returned (as an nd array), preferences should be generated here 
        pass

    def _get_arcs(self, point, reactors, suppliers):
        arcs = []
        for r_kind, r_ary in reactors.items():
            for r in r_ary:
                for commod, nodes in r.commod_to_nodes:
                    s_kind = commodities_to_suppliers[s_kind]
                    for s_ary in suppliers[s_kind]:
                        for s in s_ary:
                            arcs.append(
                                self._generate_supply(point, r_kind, commod, 
                                                      nodes, s_kind, s))
        return np.concatenate(arcs)                    

    def gen_inst(self, point):
        """Parameters
        ----------
        point :  RandomRequestPoint
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
        arcs = self._get_arcs(point, reactors, supplier)
        
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
