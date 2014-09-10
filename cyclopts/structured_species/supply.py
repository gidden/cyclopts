"""A module for defining structured supply species.

:author: Matthew Gidden <matthew.gidden _at_ gmail.com>
"""
import itertools
import numpy as np
import random
import math

from collections import OrderedDict, defaultdict, Iterable

from cyclopts import tools as cyctools
from cyclopts import cyclopts_io as cycio
import cyclopts.exchange_instance as exinst
from cyclopts.problems import ProblemSpecies
from cyclopts.exchange_family import ResourceExchange

from cyclopts.structured_species import data
from cyclopts.structured_species import tools as strtools
from cyclopts.structured_species import request

class Point(strtools.Point):
    """A container class representing a point in parameter space"""

    """ordered mapping from input parameters to default values and np.dtypes, see
    the theory manual for further explanation of the parameter names"""
    parameters = OrderedDict(sorted(request.Point.parameters.items() + {
                "d_th": strtools.Param([0.67, 0.33, 0], (np.float64, 3)),
                "d_f_mox": strtools.Param([0., 0., 1., 0.], (np.float64, 4)),
                "d_f_thox": strtools.Param([0., 0., 0., 1.], (np.float64, 4)),
                "f_repo": strtools.Param(0.1, np.float32),
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
        """ordered mapping from input parameters to default values and np.dtypes, see
        the theory manual for further explanation of the parameter names"""
        return Point.parameters

class StructuredSupply(ProblemSpecies):
    """A class representing structured supply-based exchanges species."""
    
    def __init__(self):
        super(StructuredSupply, self).__init__()
        self._family = ResourceExchange()
        self.space = None
        self._n_points = None
        # 16 bytes for uuid
        self.param_tbl_name = 'Points'
        self._param_dtype = np.dtype(
            [('paramid', ('str', 16)), ('family', ('str', 30))] + \
                [(name, param.dtype) for name, param in Point.parameters.items()])
        self.sum_tbl_name = 'Summary'
        facs = ['n_r_th', 'n_r_f_mox', 'n_r_f_thox', 'n_s_uox', 'n_s_th_mox', 
                'n_s_f_mox', 'n_s_f_thox', 'n_s_repo']
        self.iter_params = ['d_th', 'd_f_mox', 'd_f_thox']
        self._sum_dtype = np.dtype(
            [('paramid', ('str', 16)), ('family', ('str', 30))] + \
                [(name, np.uint32) for name in facs])
            
        self.nids = cyctools.Incrementer()
        self.gids = cyctools.Incrementer()
        self.arcids = cyctools.Incrementer()

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
        return 'StructuredSupply'

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
                          for k, v in space_dict.items() \
                          if k in Point.parameters}

    @property
    def n_points(self):
        """Returns
        -------
        n : int
            The total number of points in the parameter space
        """
        return cyctools.n_permutations(self.space, iter_keys=self.iter_params)
    
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
        uid = param_uuid.bytes if len(param_uuid.bytes) == 16 \
            else param_uuid.bytes + '\0' 
        data = [param_uuid.bytes, self._family.name]
        data += [getattr(point, k) for k in Point.parameters.keys()]
        tables[self.param_tbl_name].append_data([tuple(data)])
        
        data = [param_uuid.bytes, self._family.name]
        data += strtools.reactor_breakdown(point)
        data += strtools.supplier_breakdown(point)
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
        n_uox, n_t_mox, n_f_mox, n_f_thox, n_repo = strtools.supplier_breakdown(point)
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
        repo_s = np.ndarray(
            shape=(n_f_thox,), 
            buffer=np.array([Supplier(data.Supports.repo, point, self.gids) \
                                 for i in range(n_repo)]), 
            dtype=Supplier)
        suppliers = {
            data.Supports.uox: uox_s,
            data.Supports.th_mox: mox_th_s,
            data.Supports.f_mox: mox_f_s,
            data.Supports.f_thox: thox_s,
            data.Supports.repo: repo_s,
            }
        return suppliers

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
        self.nids = cyctools.Incrementer()
        self.gids = cyctools.Incrementer()
        self.arcids = cyctools.Incrementer()

        # species objects
        reactors = self._get_reactors(point)        
        suppliers = self._get_suppliers(point)        

        # create arcs
        arcs = [] #self._get_arcs(point, reactors, suppliers)
        
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
