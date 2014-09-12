"""This module defines a ProblemSpecies subclass and related classes for
reactor-request-based resources exchanges that are randomly populated (i.e., not
related to a specific fuel cycle).

:author: Matthew Gidden <matthew.gidden _at_ gmail.com>
"""
import operator
import re
import collections
import uuid
import random as rnd
import numpy as np
import copy as cp
import itertools

import cyclopts.exchange_instance as exinst
from cyclopts.problems import ProblemSpecies
import cyclopts.cyclopts_io as cycio
from cyclopts.exchange_family import ResourceExchange
from cyclopts.params import Param, BoolParam, CoeffParam, SupConstrParam, \
    PARAM_CTOR_ARGS
import cyclopts.tools as tools

class RandomRequestPoint(object):
    """A container class representing a point in parameter space for
    RandomRequest problem species.
    """
    def __init__(self, n_commods = None, 
                 n_request = None, assem_per_req = None, req_qty = None, 
                 assem_multi_commod = None, 
                 req_multi_commods = None, exclusive = None, n_req_constr = None, 
                 n_supply = None, sup_multi = None, sup_multi_commods = None, 
                 n_sup_constr = None, sup_constr_val = None, 
                 connection = None, constr_coeff = None, pref_coeff = None):
        """Parameters
        ----------
        n_commods : Param or similar, optional
            the number of commodities
        n_request : Param or similar, optional
            the number of requesters (i.e., RequestGroups)
        assem_per_req : Param or similar, optional
            the number of assemblies in a request
        req_qty : Param or similar, optional
            the quantity associated with each request
        assem_multi_commod : BoolParam or similar, optional
            whether an assembly request can be satisfied by multiple 
            commodities
        req_multi_commods : Param or similar, optional
            the number of commodities in a multicommodity zone
        exclusive : BoolParam or similar, optional
            the probability that a reactor assembly request is exclusive
        n_req_constr : Param or similar, optional
            the number of constraints associated with a given request group
        n_supply : Param or similar, optional
            the number of suppliers (i.e., supply ExchangeNodeGroups)
        sup_multi : BoolParam or similar, optional
            whether a supplier supplies more than one commodity
        sup_multi_commods : Param or similar, optional
            the number of commodities a multicommodity supplier supplies
        n_sup_constr : Param or similar, optional
            the number of constraints associated with a given supply group
        sup_constr_val : SupConstrParam or similar, optional
            the supply constraint rhs value (as a fraction of the total request 
            amount for a commodity)
        connection : BoolParam or similar, optional
            the probability that a possible connection between supply and 
            request nodes is added
        constr_coeff : CoeffParam or similar, optional
            constraint coefficients
        pref_coeff : CoeffParam or similar, optional
            preference coefficients
        """
        self.n_commods = n_commods \
            if n_commods is not None else Param(1)
        self.n_request = n_request \
            if n_request is not None else Param(1)
        self.assem_per_req = assem_per_req \
            if assem_per_req is not None else Param(1)
        self.req_qty = req_qty \
            if req_qty is not None else Param(1)
        self.assem_multi_commod = assem_multi_commod \
            if assem_multi_commod is not None else BoolParam(-1.0) # never true
        self.req_multi_commods = req_multi_commods \
            if req_multi_commods is not None else Param(0)
        self.exclusive = exclusive \
            if exclusive is not None else BoolParam(-1.0) # never true
        self.n_req_constr = n_req_constr \
            if n_req_constr is not None else Param(0)
        self.n_supply = n_supply \
            if n_supply is not None else Param(1)
        self.sup_multi = sup_multi \
            if sup_multi is not None else BoolParam(-1.0) # never true
        self.sup_multi_commods = sup_multi_commods \
            if sup_multi_commods is not None else Param(0)
        self.n_sup_constr = n_sup_constr \
            if n_sup_constr is not None else Param(1)
        self.sup_constr_val = sup_constr_val \
            if sup_constr_val is not None else SupConstrParam(1.0)
        self.connection = connection \
            if connection is not None else BoolParam(1.0)
        self.constr_coeff = constr_coeff \
            if constr_coeff is not None else CoeffParam(1e-10, 2.0)
        # 1e-10 is 'sufficiently' low
        self.pref_coeff = pref_coeff \
            if pref_coeff is not None else CoeffParam(1e-10, 1.0) 

    def __eq__(self, other):
        for k, exp in self.__dict__.items():
            if k not in other.__dict__:
                return False
            # this is a hack because for some reason for CoeffParams, a == b is
            # true and a != b is true, but I can't get corresponding behavior in
            # ipython. weird.
            if not exp == other.__dict__[k]:
                return False
        return True

    def __str__(self):
        ret = ["{0} = {1}".format(k, getattr(self, k).__str__()) \
                   for k, v in self.__dict__.items()]
        return "RandomRequestPoint\n{0}".format("\n".join(ret))

    def _dt_convert(self, obj):
        """Converts a python object to its numpy dtype. Nones are converted to
        strings, and all strings are set to size == 32.
        """
        if obj == None or isinstance(obj, basestring):
            return np.dtype('|S32')
        if isinstance(obj, collections.Sequence):
            return np.dtype('|S32')
        else:
            return np.dtype(type(obj))

    def _convert_seq(self, val):
        """converts a string representation of a sequence into a list"""
        return [float(i) for i in \
                    re.sub('[\]\[,]', '', str(val)).split()]

    def _is_seq_not_str(self, attr):
        return isinstance(attr, collections.Sequence) \
            and not isinstance(attr, basestring)

    def dtype(self):
        """Returns a numpy dtype describing all composed objects."""
        ret = [('paramid', ('str', 16)), ('family', ('str', 30))] # uuid
        for name, obj in self.__dict__.items():
            cycmembers = tools.cyc_members(obj)
            for member in cycmembers:
                ret.append(("{0}_{1}".format(name, member), 
                            self._dt_convert(getattr(obj, member))))
        return np.dtype(ret)
                
    def export_h5(self, uuid, fam_name):
        ret = [uuid.bytes, fam_name]
        for name, obj in self.__dict__.items():
            for subname, subobj in obj.__dict__.items():
                if subname.startswith('_'):
                    continue
                attr = getattr(obj, subname)
                ret.append(str(attr) if self._is_seq_not_str(attr) else attr)
        return tuple(ret)

    def valid(self):
        """Provides a best-guess estimate as to whether or not a given data
        point, as represented by this Sampler, is valid in the domain-defined
        parameter space.

        Returns
        -------
        bool
            whether the sampler's parameters form a valid point in the 
            sampler's parameter space
        """
        conditions = []
        # there must be at least as many suppliers as commodities
        conditions.append(self.n_commods.avg <= self.n_supply.avg)
        # there must be at least as many requesters as commodities
        conditions.append(self.n_commods.avg <= \
                              (1 + self.req_multi_commods.avg) * self.n_request.avg)
        # there must be at least as many commodities as possible commodities
        # requestable
        conditions.append(self.n_commods.avg > self.req_multi_commods.avg)
        
        # there must be at least as many commodities as possible commodities
        # suppliable
        conditions.append(self.n_commods.avg > self.sup_multi_commods.avg)
        return all(c for c in conditions)    
        
class RandomRequestBuilder(object):
    """A helper class to translate sampling parameters for a reactor request
    scenario into an instance of GraphParams used by the cyclopts.execute
    module.

    The params member can be populated in a single step by the populate() member
    function, or the various supply/request parameters can be generated by the
    generate_request and generate_supply member functions and then the params
    member can be populated with the appropriate arguments to the
    populate_params member function.

    This builder can be incorporated with other builders by providing the
    appropriate offsets.
    """
    def __init__(self, sampler, commod_offset = 0, req_g_offset = 0, 
                 sup_g_offset = 0, req_n_offset = 0, sup_n_offset = 0, 
                 arc_offset = 0,
                 *args, **kwargs):
        """Parameters
        ----------
        sampler : ReactorRequestSampler
            a parameter sampling container
        params : GraphParams, optional
            a pre-populated ExecParam object to populate
        commod_offset : int, optional
            an offset for commodity ids
        req_g_offset : int, optional
            an offset for request group ids
        sup_g_offset : int, optional
            an offset for supply group ids
        req_n_offset : int, optional
            an offset for request node ids
        sup_n_offset : int, optional
            an offset for supply node ids
        arc_offset : int, optional
            an offset for arc ids
        """
        self.sampler = sampler
        self.commod_offset = commod_offset
        
        self.req_g_offset = req_g_offset
        self.sup_g_offset = sup_g_offset
        self.req_n_offset = req_n_offset
        self.sup_n_offset = sup_n_offset
        self.arc_offset = arc_offset

    def valid(self):
        """Screens the provided sampler to determine if it provides a valid
        point in solution space (e.g., if parameter C requires that the sum of
        parameters A and B be less than some value, valid() will return false if
        that condition is not met).

        Returns
        -------
        b : bool
            whether the sampler's parameters form a valid point in the 
            sampler's parameter space
        """
        return len(self.commods) <= len(self.suppliers)
    
    def generate_request(self, commods, requesters, *args, **kwargs):
        """Returns all requests as a dictionary of requester ids to a list of
        assembly requests, where each assembly request is a list of id-commodity
        two-tuples that can satisfy such a request.

        Parameters
        ----------
        commods : set
            the commodities
        requesters : list
            the requesters        
        """
        s = self.sampler
        n_ids = self.req_n_ids = tools.Incrementer(self.req_n_offset)
        requests = collections.defaultdict(list)
        
        chosen_commods = set()
        for g_id in requesters:
            assems = s.assem_per_req.sample()
            assem_commods = self._assem_commods(commods, chosen_commods) # modeling assumption
            # add nodes
            for i in range(assems):
                n_nodes = len(assem_commods) if s.assem_multi_commod.sample() \
                    else 1
                mutual_reqs = []
                for j in range(n_nodes):
                    commod = assem_commods[j]
                    n_id = n_ids.next()
                    mutual_reqs.append((n_id, commod))
                    chosen_commods.add(commod)
                    self.reqs_to_commods[n_id] = commod
                    self.commods_to_reqs[commod] = n_id
                requests[g_id].append(mutual_reqs)
        return requests
                
    def generate_supply(self, commods, suppliers, *args, **kwargs):
        """Returns a mapping from supplier to a list of 2-tuples of supply node
        id and request node id and a mapping from supply group id to a list of
        commodities supplied by the supplier.

        Parameters
        ----------
        commods : set
            the commodities
        suppliers : list
            the suppliers        
        """
        # modeling assumption
        commod_assign = self._assign_supply_commods(commods, suppliers)
        # modeling assumption
        supply = self._select_supply(commod_assign)
        return supply, commod_assign

    def populate_params(self, request, supply, supplier_commods):
        """Populates params (the GraphParams structure) given known supply and
        request

        Parameters
        ----------
        request : as returned by generate_request
        supply : as returned by generate_supply
        supplier_commods : commods supplied by suppliers, as returned by
            generate_supply
        """
        s = self.sampler

        n_node_ucaps = {} # number of capacities per node
        req_qtys = {} # req node id to req qty 
        self.groups = []
        self.nodes = []
        self.arcs = []
        req = True
        bid = False

        # populate request params
        for g_id, multi_reqs in request.items():
            total_grp_qty = self._req_grp_qty(multi_reqs)
            n_constr = s.n_req_constr.sample()
            # add qty as first constraint -- required for clp/cbc
            caps = np.append(total_grp_qty, self._req_constr_vals(n_constr, multi_reqs))
            grp = exinst.ExGroup(g_id, req, total_grp_qty)
            for cap in caps:
                grp.AddCap(cap)
            self.groups.append(grp)
            
            exid = tools.Incrementer()
            for reqs in multi_reqs: # mutually satisfying requests
                for n_id, commod in reqs:
                    n_node_ucaps[n_id] = n_constr
                    req_qty = self._req_node_qty()
                    excl = s.exclusive.sample() # exclusive or not
                    excl_id = exid.next() if excl else -1 # need unique exclusive id
                    self.nodes.append(
                        exinst.ExNode(n_id, g_id, req, req_qty, excl, excl_id))
                    req_qtys[n_id] = req_qty
    
        # populate supply params and arc relations
        a_ids = tools.Incrementer(self.arc_offset)
        commod_demand = self._commod_demand()
        supplier_capacity = \
            self._supplier_capacity(commod_demand, supplier_commods)
        for g_id, sups in supply.items():
            caps = self._sup_constr_vals(supplier_capacity[g_id], 
                                         s.n_sup_constr.sample())
            grp = exinst.ExGroup(g_id, bid)
            for cap in caps:
                grp.AddCap(cap)
            self.groups.append(grp)
            for v_id, u_id in sups:
                req_qty = req_qtys[u_id]
                n_node_ucaps[v_id] = len(caps)
                self.nodes.append(exinst.ExNode(v_id, g_id, bid, req_qty))
                # arc from u-v node
                # add qty as first constraint -- required for clp/cbc
                ucaps = np.append(
                    [self._req_def_constr(req_qty)], 
                    [s.constr_coeff.sample() for i in range(n_node_ucaps[u_id])])
                vcaps = [s.constr_coeff.sample() for i in range(n_node_ucaps[v_id])]
                self.arcs.append(
                    exinst.ExArc(a_ids.next(), u_id, ucaps, 
                                 v_id, vcaps, s.pref_coeff.sample()))

        return self.groups, self.nodes, self.arcs

    def build(self, *args, **kwargs):
        """Builds Group, Node, and Arc components of a Reactor-Request based
        Resource Exchange
        """
        s = self.sampler
        commods = self.commods = \
            set(range(self.commod_offset, 
                      self.commod_offset + s.n_commods.sample()))
        self.n_request = s.n_request.sample() # number of request groups
        self.n_supply = s.n_supply.sample() # number of supply groups
        # the request quantity per assembly (i.e., kg of fuel per assembly request)
        self.req_qty = s.req_qty.sample() 

        req_g_ids = tools.Incrementer(self.req_g_offset)
        # request groups
        requesters = self.requesters = \
            [req_g_ids.next() for i in range(self.n_request)] 
        # include request values because ids are global
        sup_g_ids = \
            tools.Incrementer(self.req_g_offset + self.sup_g_offset + self.n_request)
        # supply groups
        suppliers = self.suppliers = \
            [sup_g_ids.next() for i in range(self.n_supply)] 
        self.arc_ids = tools.Incrementer(self.arc_offset)

        self.reqs_to_commods = {} # requests to their commodities
        self.commods_to_reqs = {} # commodities to all requests
        self.sups_to_commods = {} # supply to their commodities

        request = self.generate_request(commods, requesters)
        supply, supplier_commods = self.generate_supply(commods, suppliers)

        requested_commods = set(v for k, v in self.reqs_to_commods.items())
        supplied_commods = set(v for k, v in self.sups_to_commods.items())
        if (requested_commods != set(commods)):
            raise ValueError(("All commmodities are not requested; "
                              "Commodities: {0}, "
                              "requested commodities {1}.".format(
                        set(commods), requested_commods)))
        if (supplied_commods != set(commods)):
            raise ValueError(("All commmodities are not supplied; "
                              "Commodities: {0}, "
                              "supplied commodities {1}.".format(
                        set(commods), supplied_commods)))
        return self.populate_params(request, supply, supplier_commods)
    
    #
    # Encapsulated assumptions
    #
    def _assem_commods(self, commods, chosen_commods = set()):
        """Returns a list of commodities that satisfy assembly requests with the
        primary commodity as the first element. This is a basic modeling
        assumption for reactor request exchange building.

        Parameters
        ----------
        chosen_commods : set
            a set of commodities that have already been chosen; this set is used 
            to guarantee that there is at least one requester for each commodity
        commods : set
            the commodities
        """
        s = self.sampler
        left = cp.deepcopy(commods)
        
        # choose a new commodity if we need to, otherwise choose a random one
        if len(chosen_commods) != len(commods):
            pool = commods.difference(chosen_commods)
            first_commod = rnd.sample(pool, 1)[0]
        else:
            first_commod = rnd.sample(left, 1)[0]
        assem_commods = [first_commod]
        left.remove(first_commod)
        # other commodities for assemblies that can be satisfied by 
        # multiple commodities
        assem_commods += rnd.sample(left, s.req_multi_commods.sample())
        return assem_commods

    def _assign_supply_commods(self, commods, suppliers):
        """Returns a mapping from supplier to a list commodities it
        supplies. This is a basic modeling assumption for reactor request
        exchange building.

        Parameters
        ----------
        commods : set
            the commodities
        suppliers : list
            the suppliers
        """
        if len(commods) > len(suppliers):
            raise ValueError("There must be at least as many suppliers as commodities.")

        s = self.sampler
        c_list = list(commods)
        rnd.shuffle(c_list) # get a random ordering
        assign = {}
        i = 0
        # give each supplier a primary commodity, guaranteeing that all
        # commodities have at least one supplier, and some number of randomly
        # sampled secondary commodities if applicable
        for sup in suppliers:
            primary = c_list[i % len(commods)]
            i += 1
            n_extra = s.sup_multi_commods.sample() \
                if s.sup_multi.sample() else 0
            pool = cp.copy(commods)
            pool.remove(primary)
            secondaries = rnd.sample(pool, n_extra)
            assign[sup] = [primary] + secondaries
        return assign

    def _select_supply(self, commod_assign):
        """Returns a mapping from supplier to a list of 2-tuples of supply node
        id and request node id. This is a basic modeling assumption for sreactor
        request exchange building.

        Parameters
        ----------
        commod_assign : as returned by _assign_supply_commods
        """
        s = self.sampler

        # include request values because ids are global
        n_ids = self.sup_n_ids = tools.Incrementer(self.req_n_offset + 
                                                   self.sup_n_offset + 
                                                   len(self.reqs_to_commods))

        supply = collections.defaultdict(list) # supplier group id to arcs
        possible_supply = collections.defaultdict(list) # req to supplier group id
        for g_id, g_commods in commod_assign.items():
            for req, commod in self.reqs_to_commods.items():
                if commod in g_commods:
                    possible_supply[req].append(g_id)

        for req, g_ids in possible_supply.items():
            rnd.shuffle(g_ids)
            # guarantees all reqs are connected to at least 1 supplier
            s_id = n_ids.next()
            supply[g_ids[0]].append((s_id, req))
            self.sups_to_commods[s_id] = self.reqs_to_commods[req]
            for i in range(1, len(g_ids)):
                if s.connection.sample():
                    s_id = n_ids.next()
                    supply[g_ids[i]].append((s_id, req))
                    self.sups_to_commods[s_id] = self.reqs_to_commods[req]
        return supply

    def _req_grp_qty(self, reqs):
        """Returns the request quantity for a request group.

        Parameters
        ----------
        reqs : list
            the requests associated with the group
        """
        # assumes 1 assembly == 1 mass unit, all constr vals equivalent. note
        # that reqs = [ [satisfying commods] ], so one entry per actual request
        return self.req_qty * len(reqs)

    def _req_constr_vals(self, n_constr, reqs):
        """Returns a list of rhs constraint values for a request group.

        Parameters
        ----------
        n_constr : int
            the number of constraints for the group
        reqs : list
            the requests associated with the group
        """
        # note that reqs = [ [satisfying commods] ], so one entry per actual
        # request
        constr_val = len(reqs)
        return np.array([constr_val for i in range(n_constr)])
    
    def _req_node_qty(self):
        """Returns the quantity for an individual request."""
        # change these if all assemblies have mass != 1
        return self.req_qty
    
    def _req_def_constr(self, req_qty):
        """Returns the default unit constraint value for a request.

        Parameters
        ----------
        req_qty : float
            the request quantity
        """
        # change these if all assemblies have mass != 1 
        # ---
        # ^ I don't actually think so, this looks like the unit capacity, which
        # should always be 1 if all requests have the same mass
        return 1

    def _commod_demand(self):
        """Returns a mapping from commodities to the total demand of all nodes
        for that commodity.
        """
        commod_demand = collections.defaultdict(float)
        for req, commod in self.reqs_to_commods.items():
            commod_demand[commod] += 1 # need to change if assembly size != 1
        return commod_demand

    def _supplier_capacity(self, commod_demand, supplier_commods):
        """Returns a mapping from suppliers to their maximum supply
        capacity. 

        Parameters
        ----------
        commod_demand : dict
            a mapping of commodity to total demand over all request nodes
        supplier_commods : dict
            a mapping of suppliers to the commodities they supply

        Details
        -------
        The maximum supply capacity is calculated as the maximum demand for all
        commodities that can be supplied.
        """
        factor = self.req_qty
        return {sup: factor * max([commod_demand[c] for c in commods]) \
                    for sup, commods in supplier_commods.items()}

    def _sup_constr_vals(self, capacity, n_constr):
        """Returns a list of rhs constraint values for a supplier.

        Parameters
        ----------
        capacity : float
            the baseline supplier capacity
        n_constr : int
            the number of constraints
        """
        # assumes that all supplier constraint values are based of a baseline
        # constraint value
        s = self.sampler
        return np.array([s.sup_constr_val.sample() * capacity \
                             for i in range(n_constr)])

class RandomRequest(ProblemSpecies):
    """A problem species for random (non-fuel cycle specific) reactor request
    exchanges."""

    def __init__(self):
        super(RandomRequest, self).__init__()
        self._params_it = None
        self._n_points = None
        self.tbl_name = 'RandomRequestParameters'

    def _get_param_dict(self, rc_dict):
        """Provides a dictionary of parameter names to all constructor arguments
        for a resource exchange range of instances.
        
        Parameters
        ----------
        rc_dict : dict
            A dictionary of attributes, e.g. from a RunControl object
        
        Returns
        -------
        params_dict : dict
            A dictionary whose keys are parameter names and values are lists of
            ranges of constructor arguments.
        """
        params_dict = {}
        s = RandomRequestPoint()
        for k, v in rc_dict.items():
            name = k
            attr = v
            if hasattr(s, name):
                vals = []
                args = PARAM_CTOR_ARGS[type(getattr(s, name))]
                for arg in args:
                    if arg in attr:
                        vals += [attr[arg]]
                if len(vals) > 0:
                    params_dict[name] = vals
            else:
                print("Found an entry named {0} that "
                      "is unknown to the parser.".format(k))
                
        return params_dict

    def _param_gen(self, params_dict):
        """Returns input for _add_subtree() given input for build()"""
        params_dict = {k: [i for i in itertools.product(*v)] \
                           for k, v in params_dict.items()}
        s = RandomRequestPoint()
        for k, v in params_dict.items():
            yield k, [type(getattr(s, k))(*args) for args in v]

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
        return 'RandomRequest'

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
        return [cycio.Table(h5file, 
                            '/'.join([prefix, self.tbl_name]),
                            RandomRequestPoint().dtype())]

    def read_space(self, space_dict):
        """Parameters
        ----------
        space_dict : dict
            A dictionary container resulting from the reading in of a run 
            control file
        """
        pdict = self._get_param_dict(space_dict)
        self._n_points = reduce(operator.mul, 
                                (len(l) for _, val in pdict.iteritems() \
                                     for l in val), 1)
        self._params_it = self._param_gen(pdict)
        
    @property
    def n_points(self):
        """Returns
        -------
        n : int
            The total number of points in the parameter space
        """
        return self._n_points
    
    def points(self):
        """Returns
        -------
        point : RandomRequestPoint
            A representation of a point in parameter space to be used by this 
            species
        """
        pairings = [[(name, param) for param in params] \
                        for name, params in self._params_it]
        for prod in itertools.product(*pairings):
            point = RandomRequestPoint()
            for name, param in prod:
                setattr(point, name, param)
            if point.valid():
                yield point

    def record_point(self, point, param_uuid, tables):
        """Parameters
        ----------
        point : RandomRequestPoint
            A representation of a point in parameter space
        param_uuid : uuid
            The uuid of the point in parameter space
        tables : list of cyclopts_io.Table
            The tables that can be written to
        """
        tables[self.tbl_name].append_data(
            [point.export_h5(param_uuid, self.family.name)])
        
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
        builder = RandomRequestBuilder(point)
        builder.build()
        return builder.groups, builder.nodes, builder.arcs
