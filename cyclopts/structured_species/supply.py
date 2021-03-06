"""A module for defining structured supply species.

:author: Matthew Gidden <matthew.gidden _at_ gmail.com>
"""
import itertools
import numpy as np
import random
import math

from collections import OrderedDict, defaultdict, Iterable, namedtuple

from cyclopts import tools as cyctools
from cyclopts import cyclopts_io as cycio
from cyclopts import io_tools as io_tools
import cyclopts.exchange_instance as exinst
from cyclopts.problems import ProblemSpecies
from cyclopts.exchange_family import ResourceExchange

from cyclopts.structured_species import data
from cyclopts.structured_species import tools as strtools
from cyclopts.structured_species import request

def commod_to_reqrs(fidelity):
    """return a mapping of commodities to requesters of those commodities"""
    ret = defaultdict(list)
    min_fidelities = {
        data.Supports.th_mox: 0,
        data.Supports.f_mox: 1,
        data.Supports.f_thox: 2,
        data.Supports.repo: 0,
        }
    for reqr, v in data.sup_pref_basis.items():
        if not fidelity >= min_fidelities[reqr]:
            continue
        commods = v.keys()
        for c in commods:
            ret[c].append(reqr)
    return ret

class Point(strtools.Point):
    """A container class representing a point in parameter space"""

    """ordered mapping from input parameters to default values and np.dtypes, see
    the theory manual for further explanation of the parameter names"""
    parameters = OrderedDict(sorted(request.Point.parameters.items() + {
                "d_th": strtools.Param([0.67, 0.33, 0], (np.float64, 3)),
                "d_f_mox": strtools.Param([0., 0., 1., 0.], (np.float64, 4)),
                "d_f_thox": strtools.Param([0., 0., 0., 1.], (np.float64, 4)),
                "r_repo": strtools.Param(0.1, np.float32),
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
    def __init__(self, kind, point=None, n_assems=None):
        super(Reactor, self).__init__(kind, point, n_assems)
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
    def __init__(self, kind, gids, nids):
        self.kind = kind
        self.req_qty = data.sup_rhs[self.kind]
        gid = gids.next()
        req = True
        self.group = grp = exinst.ExGroup(gid, req, self.req_qty)
        grp.AddCap(self.req_qty)
        if self.kind != data.Supports.repo:
            commod = data.sup_to_commod[self.kind]
            rxtr = data.sup_to_rxtr[self.kind]
            grp.AddCap(self.req_qty * strtools.mean_enr(rxtr, commod) / 100. \
                           * data.relative_qtys[rxtr][commod])
        self._gen_nodes(gid, nids)
        self.loc = data.loc()
        
    def _gen_nodes(self, gid, nids):
        self.nodes = []
        self.commod_to_nodes = {}
        req = True
        for commod in data.sup_pref_basis[self.kind].keys():
            nid = nids.next()
            node = exinst.ExNode(nid, gid, req, self.req_qty)
            self.nodes.append(node)
            self.commod_to_nodes[commod] = node

    def coeff(self, enr, rkind, commod):
        if self.kind == data.Supports.repo:
            raise RuntimeError('Coeff not supported for repos')
        return enr / 100. * data.relative_qtys[rkind][commod] 
        
class PathMap(io_tools.PathMap):
    """A simple container class for mapping columns to Hdf5 paths
    implemented for the StructuredSupply problem species"""
    
    def __init__(self, col):
        super(PathMap, self).__init__(col)
        
    @property
    def path(self):
        # this is an approx. heuristic, it might need to be updated
        inst = StructuredSupply()
        if self.col.startswith('n_'):
            tbl = inst.sum_tbl_name
        elif self.col.endswith('pref_flow') or self.col.endswith('cost_flow') :
            tbl = strtools.pp_tbl_name
        else:
            tbl = inst.param_tbl_name
        return '/'.join([inst.io_prefix, tbl])

class StructuredSupply(ProblemSpecies):
    """A class representing structured supply-based exchanges species."""

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
        return 'StructuredSupply'

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

    @staticmethod
    def pnt_to_realization(point):
        """Returns a realization of a structured supply instance given a point
        in parameter space.
        
        A realization is a namedtuple of :
          * reqrs: a dictionary of the kind and number of each requester
          * rxtrs: a dictionary of the kind and number of each reactor
          * assem_dists: a dictionary of the kind of reactor to a dictionary 
            of Commodity type to the number of assemblies of that Commodity type
        """
        # skip uox support facilities
        reqrs = {data.Supports[i]: n \
                     for i, n in enumerate(strtools.support_breakdown(point)) \
                     if i in data.sup_pref_basis.keys()}
        rxtrs = {data.Reactors[i]: n \
                     for i, n in enumerate(strtools.reactor_breakdown(point))}
        dists = {k: strtools.assembly_breakdown(point, k) \
                     for k in data.Reactors}
        keys = ['n_reqrs', 'n_rxtrs', 'assem_dists']
        return namedtuple('Realization', keys)(reqrs, rxtrs, dists)

    @staticmethod
    def gen_arc(aid, point, commod, rx_node_id, rxtr, reqr, instid=None, arc_tbl=None):
        """generate an arc"""
        commod_pref = data.sup_pref_basis[reqr.kind][commod]
        loc_pref = strtools.loc_pref(rxtr.loc, reqr.loc, point.f_loc, point.n_reg)
        pref = commod_pref + loc_pref * point.r_l_c
        if arc_tbl is not None:
            arc_tbl.append_data([(aid, commod, commod_pref, loc_pref)])
        # unit capacity for total mass constraint first
        rq_coeffs = [1., reqr.coeff(rxtr.enr(commod), rxtr.kind, commod)] \
            if not reqr.kind == data.Supports.repo else [1.]
        arc = exinst.ExArc(aid,
                           reqr.commod_to_nodes[commod].id, rq_coeffs,
                           rx_node_id, [1],
                           pref)
        return arc
    
    def __init__(self):
        super(StructuredSupply, self).__init__()
        self.space = None
        self._n_points = None
        # 16 bytes for uuid
        self._param_dtype = np.dtype(
            [('paramid', ('str', 16)), ('family', ('str', 30))] + \
                [(name, param.dtype) for name, param in Point.parameters.items()])
        facs = ['n_r_th', 'n_r_f_mox', 'n_r_f_thox', 'n_s_uox', 'n_s_th_mox', 
                'n_s_f_mox', 'n_s_f_thox', 'n_s_repo']
        self.iter_params = ['d_th', 'd_f_mox', 'd_f_thox']
        self._sum_dtype = np.dtype(
            [('paramid', ('str', 16)), ('family', ('str', 30))] + \
                [(name, np.uint32) for name in facs])
        # reset id generation
        self.nids = cyctools.Incrementer()
        self.excl_ids = cyctools.Incrementer()
        self.gids = cyctools.Incrementer()
        self.arcids = cyctools.Incrementer()
        self.instid = None
        self.tables = None

        # default realization is None
        self._rlztn = None

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
        for k in keys:
            if k in self.iter_params:
                # iterable params must be iterable
                if not cyctools.seq_not_str(self.space[k]):
                    raise RuntimeError('{0} entry must be a Sequence'.format(k))
                # if they are defined as a single value, make them a sequence
                if not cyctools.seq_not_str(self.space[k][0]):
                    self.space[k] = [self.space[k]]
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
        data += strtools.support_breakdown(point)
        tables[self.sum_tbl_name].append_data([tuple(data)])

    def _get_reactors(self):
        # requires self._rlztn to be set
        rkinds = self._rlztn.n_rxtrs.keys()
        n_assems = {k: sum(v.values()) \
                       for k, v in self._rlztn.assem_dists.items()}
        gen_ary = lambda kind, num, n_assems: \
            np.ndarray(
            shape=(num,), 
            buffer=np.array([Reactor(kind, n_assems=n_assems) \
                                 for i in range(num)]), 
            dtype=Reactor)
        return {k: gen_ary(k, self._rlztn.n_rxtrs[k], n_assems[k]) \
                    for k in rkinds}

    def _get_requesters(self):
        # requires self._rlztn to be set
        gen_ary = lambda kind, num: \
            np.ndarray(
            shape=(num,), 
            buffer=np.array([Requester(kind, self.gids, self.nids) \
                                 for i in range(num)]), 
            dtype=Requester)
        return {k: gen_ary(k, v) for k, v in self._rlztn.n_reqrs.items()}

    def _gen_structure(self, point, reactors, requesters):
        # requires self._rlztn to be set
        grps, nodes, arcs = [], [], []
        for rx_kind, rx_ary in reactors.items():
            for rxtr in rx_ary:
                for commod, nassems in self._rlztn.assem_dists[rx_kind].items():
                    for i in range(nassems):
                        excl_id = self.excl_ids.next()
                        gid = self.gids.next()
                        grp = rxtr.gen_group(gid)
                        grps.append(grp)
                        for rq_kind in self.commod_to_reqrs[commod]:
                            if rq_kind not in requesters:
                                continue
                            for reqr in requesters[rq_kind]:
                                nid = self.nids.next()
                                node = rxtr.gen_node(nid, gid, excl_id)
                                arc = StructuredSupply.gen_arc(
                                    self.arcids.next(), point, commod, 
                                    nid, rxtr, reqr, self.instid, self.arc_tbl) 
                                nodes.append(node)
                                arcs.append(arc)
        return grps, nodes, arcs

    def gen_inst(self, point, instid=None, io_manager=None, reset_rlztn=True):
        """Parameters
        ----------
        point :  structured_species.Point
            A representation of a point in parameter space
        instid : uuid, optional
            the id for the instance
        io_manager : cyclopts_io.IOManager, optional
            IOManager that gives access to tables/groups for writing
        reset_rltzn : bool, optional
            Reset the internal realization
           
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

        self.commod_to_reqrs = commod_to_reqrs(point.f_fc)
        
        # species objects
        if self._rlztn is None or reset_rlztn: 
            # this could have been set before calling gen_inst, e.g., for 
            # testing
            self._rlztn = StructuredSupply.pnt_to_realization(point)
        reactors = self._get_reactors()    
        requesters = self._get_requesters()
        
        # structure
        rx_groups, rx_nodes, arcs = self._gen_structure(point, reactors, requesters)
        if self.arc_tbl is not None:
            self.arc_tbl.flush()
        
        # combine groups, nodes
        groups = np.concatenate(
            (rx_groups, 
             [x.group for ary in requesters.values() for x in ary]))
        nodes = np.concatenate(
            (rx_nodes, 
             [n for ary in requesters.values() for x in ary for n in x.nodes]))

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
