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

class Reactor(strtools.Reactor):
    """An extension reactor model for Structured Supply Species"""
    def __init__(self, kind, point):
        super(Reactor, self).__init__(kind, point)
        self.assem_qty = data.fuel_unit * data.core_vol_frac[self.kind] \
            / self.n_assems

    def gen_group(self, gid):
        supply = False
        grp = exinst.ExGroup(gid, supply)  
        grp.AddCap(self.assem_qty)
        return grp

    def gen_node(self, nid, gid, excl_id):
        supply = False
        excl = True
        return exinst.ExNode(nid, gid, supply,  
                             self.assem_qty, excl, excl_id)

class Requester(object):
    """A simplified requester model for Structured Supply Species"""
    def __init__(self, kind, point, gids, nids):
        self.kind = kind
        self.req_qty = data.sup_rhs[self.kind]
        gid = gids.next()
        req = True
        if self.kind == data.Supports.repo:
            self.group = grp = exinst.ExGroup(gid, req, self.req_qty)
        else:
            self.group = grp = exinst.ExGroup(gid, req, self.req_qty)
            commod = data.sup_to_commod[self.kind]
            rxtr = data.sup_to_rxtr[self.kind]
            mean_enr = strtools.mean_enr(rxtr, commod)
            grp.AddCap(self.req_qty * mean_enr * data.relative_qtys[rxtr][commod])
        self._gen_nodes(point, gid, nids)
        self.loc = data.loc()

    def _gen_nodes(self, point, gid, nids):
        self.nodes = []
        self.commod_to_nodes = {}
        req = True
        for commod in data.sup_pref_basis[self.kind].keys():
            nid = nids.next()
            node = exinst.ExNode(nid, gid, req, self.req_qty)
            self.nodes.append(node)
            self.commod_to_nodes[commod] = node

    def coeffs(self, qty, enr):
        pass

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
        data += strtools.support_breakdown(point)
        tables[self.sum_tbl_name].append_data([tuple(data)])

    def _get_reactors(self, point):
        n_uox, n_mox, n_thox = strtools.reactor_breakdown(point)
        uox_th_r = np.ndarray(
            shape=(n_uox,), 
            buffer=np.array([Reactor(data.Reactors.th, point) \
                                 for i in range(n_uox)]), 
            dtype=Reactor)
        mox_f_r = np.ndarray(
            shape=(n_mox,), 
            buffer=np.array([Reactor(data.Reactors.f_mox, point) \
                                 for i in range(n_mox)]), 
            dtype=Reactor)
        thox_f_r = np.ndarray(
            shape=(n_thox,), 
            buffer=np.array([Reactor(data.Reactors.f_thox, point) \
                                 for i in range(n_thox)]), 
            dtype=Reactor)
        reactors = {
            data.Reactors.th: uox_th_r,
            data.Reactors.f_mox: mox_f_r,
            data.Reactors.f_thox: thox_f_r,
            }
        return reactors

    def _get_requesters(self, point):
        n_uox, n_t_mox, n_f_mox, n_f_thox, n_repo = strtools.support_breakdown(point)
        uox_s = np.ndarray(
            shape=(n_uox,), 
            buffer=np.array([Requester(data.Supports.uox, point, self.gids) \
                                 for i in range(n_uox)]), 
            dtype=Requester)
        mox_th_s = np.ndarray(
            shape=(n_t_mox,), 
            buffer=np.array([Requester(data.Supports.th_mox, point, self.gids) \
                                 for i in range(n_t_mox)]), 
            dtype=Requester)
        mox_f_s = np.ndarray(
            shape=(n_f_mox,), 
            buffer=np.array([Requester(data.Supports.f_mox, point, self.gids) \
                                 for i in range(n_f_mox)]), 
            dtype=Requester)
        thox_s = np.ndarray(
            shape=(n_f_thox,), 
            buffer=np.array([Requester(data.Supports.f_thox, point, self.gids) \
                                 for i in range(n_f_thox)]), 
            dtype=Requester)
        repo_s = np.ndarray(
            shape=(n_f_thox,), 
            buffer=np.array([Requester(data.Supports.repo, point, self.gids) \
                                 for i in range(n_repo)]), 
            dtype=Requester)
        requesters = {
            data.Supports.uox: uox_s,
            data.Supports.th_mox: mox_th_s,
            data.Supports.f_mox: mox_f_s,
            data.Supports.f_thox: thox_s,
            data.Supports.repo: repo_s,
            }
        return requesters

    def assembly_breakdown(self, point, kind):
        # todo: finish; commod: n assemblies
        pass

    def _gen_arc(self, point, commod, rxnode, rxtr, reqr):
        pref = strtools.preference(data.sup_pref_basis[reqr.kind][commod], 
                                   rxtr.loc, reqr.loc, 
                                   point.f_loc, point.r_l_c, point.n_reg)
        arc = exinst.ExArc(self.arcids.next(),
                           reqr.node.id, reqr.coeffs(rxnode.qty, rxtr.enr(commod)),
                           rxnode.id, [1],
                           pref)
        return arc

    def _gen_structure(self, point, reactors, requesters):
        grps, nodes, arcs = [], [], []
        for rx_kind, rx_ary in reactors:
            assems = self.assembly_breakdown(point, rx_kind)
            for rxtr in rx_ary:
                for commod, nassems in assems:
                    for i in range(nassems):
                        excl_id = self.excl_ids.next()
                        gid = self.gids.next()
                        grp = rxtr.gen_group(gid)
                        grps.append(grp)
                        for reqr in requesters[commod]:
                            nid = self.nids.next()
                            node = rxtr.gen_node(nid, gid, excl_id)
                            arc = self._gen_arc(commod, node, rxtr, reqr) 
                            nodes.append(node)
                            arcs.append(arc)
        return grps, nodes, arcs

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
        self.excl_ids = cyctools.Incrementer()
        self.gids = cyctools.Incrementer()
        self.arcids = cyctools.Incrementer()

        # species objects
        reactors = self._get_reactors(point)        
        requesters = self._get_requesters(point)        

        # structure
        rq_groups = [x.group for ary in requesters.values() for x in ary]
        rq_nodes = np.concatenate([x.nodes for ary in requesters.values() \
                                       for x in ary])
        rx_groups, rx_nodes, arcs = self._gen_structure(point, reactors, requesters)

        groups = np.concatenate((rx_groups, rq_groups))
        nodes = np.concatenate((rx_nodes, rq_nodes))

        return groups, nodes, arcs
