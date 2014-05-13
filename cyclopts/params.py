"""Implements a robust interface for translating scaling parameters into a full
parameter definition of a resource exchange graph in Cyclus.

This module's core objects are the ReactorRequestBuilder and
ReactorSupplyBuilder, which provide functionality to build instances of resource
exchanges parameters that can be used to execute exchanges in Cyclus via the
execute module.

The Builders are provided sampling parameters via Sampler container objects,
which are populated with Param (or similar) objects. The Builders sample
required values through their Sampler in order to build the exchange parameter
instance.

Key modeling assumptions regarding how exchange instances are built are
separated into individual functions on the Builder's interface.  

:author: Matthew Gidden <matthew.gidden@gmail.com>
"""

import random as rnd
import numpy as np
import copy as cp
import re
import collections

try:
    from execute import GraphParams
except ImportError as e:
    print("Caught import error, "
          "are you running from the root Cyclopts directory?")
    raise e

class Incrementer(object):
    """A simple helper class to increment a value"""
    def __init__(self, start = 0):
        """Parameters
        ----------
        start : int, optional
            an initial value
        """
        self._val = start - 1

    def next(self):
        """Returns an incremented value"""
        self._val += 1
        return self._val

class Param(object):
    """A base class for sampled parameters.
    """
    def __init__(self, avg, dist = None):
        self.avg = avg
        self.dist = dist

    def sample(self):
        # if self.dist is None:
        #     return self.avg
        return self.avg

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return str(self.__dict__)

class BoolParam(object):
    """A class to sample binary events
    """
    def __init__(self, cutoff, dist = None):
        """Parameters
        ----------
        cutoff : float
            the probability cutoff, must be in (0, 1]
        """
        self.cutoff = float(cutoff)
        self.dist = dist

    def sample(self):
        """Returns True if sampled below the cutoff, False otherwise"""
        return self.cutoff >= rnd.uniform(0, 1)

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return str(self.__dict__)

class CoeffParam(object):
    """A class to sample coefficient values
    """
    def __init__(self, lb = 0, ub = 1, dist = None):
        """Parameters
        ----------
        lb : float
            the coefficient lower bound
        ub : float
            the coefficient upper bound
        dist :str
            the distribution to use, default is uniform
        """
        self.lb = float(lb)
        self.ub = float(ub)
        self.dist = dist if dist is not None else "uniform"

    def sample(self):
        """Returns a sampled coefficient"""
        if self.dist == "uniform":
            return rnd.uniform(self.lb, self.ub)
        else:
            raise ValueError("Unrecognized distribution: " + self.dist)

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return str(self.__dict__)

class SupConstrParam(object):
    """A base class for sampled supply constraint values.
    """
    def __init__(self, cutoff, rand = False, fracs = None):
        """Parameters
        ----------
        cutoff : float
            the lowest supply fraction
        rand : bool
            if True, a random supply fraction greater than or equal to the 
            cutoff is provided during sampling; if False, the cutoff fraction 
            is used
        fracs : list
            a collection of fractional values of commodity demand that the 
            supply constraint value could take; default is [0.25, 0.5, 0.75, 1]
        """
        self.cutoff = float(cutoff)
        self.rand = bool(rand)
        # possible supply fractions
        fracs = fracs if fracs is not None else [0.25, 0.5, 0.75, 1] 
        self.fracs = [frac for frac in fracs if frac >= cutoff]

    def sample(self):
        """Returns a fractional supply constraint value for a commodity"""
        if self.rand:
            return rnd.choice(self.fracs)
        else:
            return self.cutoff

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return str(self.__dict__)

#
# we must build this container manually, rather than inspecting instances
# see http://stackoverflow.com/questions/7628081/how-to-get-arguments-list-of-a-built-in-python-class-constructor
#
CONSTR_ARGS = {
    Param: ['avg', 'dist'],
    BoolParam: ['cutoff', 'dist'],
    CoeffParam: ['lb', 'ub', 'dist'],
    SupConstrParam: ['cutoff', 'rand', 'fracs'],
}        

class ReactorRequestSampler(object):
    """A container class for holding all sampling objects for reactor request
    scenarios.
    """
    def __init__(self, n_commods = None, 
                 n_request = None, assem_per_req = None, 
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
            if constr_coeff is not None else CoeffParam(1e-10, 1.0)
        # 1e-10 is 'sufficiently' low
        self.pref_coeff = pref_coeff \
            if pref_coeff is not None else CoeffParam(1e-10, 1.0) 

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __str__(self):
        ret = ["{0} = {1}".format(k, getattr(self, k).__str__()) \
                   for k, v in self.__dict__.items()]
        return "ReactorRequestSampler\n{0}".format("\n".join(ret))

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

    def describe_h5(self):
        """Returns a numpy dtype describing all composed objects."""
        # np.dtype([("{0}_{1}".format(name, subname), self._dt_convert(subobj)) \
        #               for subname, subobj in obj.__dict__.items() \
        #               for name, obj in self.__dict__.items()])
        ret = []
        for name, obj in self.__dict__.items():
            for subname, subobj in obj.__dict__.items():
                ret.append(("{0}_{1}".format(name, subname), 
                            self._dt_convert(subobj)))
        return np.dtype(ret)

    def _is_seq_not_str(self, attr):
        return isinstance(attr, collections.Sequence) \
            and not isinstance(attr, basestring)
    
    def import_h5(self, row):
        for name, obj in self.__dict__.items():
            for subname, subobj in obj.__dict__.items():
                attr = getattr(obj, subname)
                val = row["{0}_{1}".format(name, subname)]
                if val == 'None':
                    val = None
                elif self._is_seq_not_str(attr):
                    val = self._convert_seq(val)
                #print("setting", "{0}.{1}".format(name, subname), "to", val)
                setattr(obj, subname, val)

    def export_h5(self, row):
        for name, obj in self.__dict__.items():
            for subname, subobj in obj.__dict__.items():
                attr = getattr(obj, subname)
                row["{0}_{1}".format(name, subname)] = \
                    str(attr) if self._is_seq_not_str(attr) else attr

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
        
class ReactorRequestBuilder(object):
    """A helper class to translate sampling parameters for a reactor request
    scenario into an instance of GraphParams used by the cyclopts.execute
    module.

    The params member can be populated in a single step by the populate() member
    function, or the various supply/request parameters can be generated by the
    generate_ member functions and then the params member can be populated with
    the appropriate arguments to the populate_params member function.

    This builder can be incorporated with other builders by providing the
    appropriate offsets.
    """
    def __init__(self, sampler, params = None, commod_offset = 0, 
                 req_g_offset = 0, 
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
        s = self.sampler = sampler
        self.commod_offset = commod_offset
        self.params = params if params is not None else GraphParams()

        self.commods = set(range(self.commod_offset, 
                                 self.commod_offset + s.n_commods.sample()))
        self.n_request = s.n_request.sample() # number of request groups
        self.n_supply = s.n_supply.sample() # number of supply groups
        
        self.req_g_offset = req_g_offset
        self.sup_g_offset = sup_g_offset
        self.req_n_offset = req_n_offset
        self.sup_n_offset = sup_n_offset
        self.arc_offset = arc_offset

        req_g_ids = Incrementer(req_g_offset)
        # request groups
        self.requesters = [req_g_ids.next() for i in range(self.n_request)] 
        # include request values because ids are global
        sup_g_ids = Incrementer(req_g_offset + sup_g_offset + self.n_request)
        # supply groups
        self.suppliers = [sup_g_ids.next() for i in range(self.n_supply)] 
        self.arc_ids = Incrementer(arc_offset)

        self.reqs_to_commods = {} # requests to their commodities
        self.commods_to_reqs = {} # commodities to all requests
        self.sups_to_commods = {} # supply to their commodities

    def valid(self):
        """Screens the provided sampler to determine if it provides a valid
        point in solution space (e.g., if parameter C requires that the sum of
        parameters A and B be less than some value, valid() will return false if
        that condition is not met).

        Returns
        -------
        bool
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
        n_ids = self.req_n_ids = Incrementer(self.req_n_offset)
        requests = collections.defaultdict(list)
        
        chosen_commods = set()
        for g_id in requesters:
            assems = s.assem_per_req.sample()
            assem_commods = self._assem_commods(commods, chosen_commods) # modeling assumption
            chosen_commods.update(assem_commods)
            # add nodes
            for i in range(assems):
                n_nodes = len(assem_commods) if s.assem_multi_commod.sample() \
                    else 1
                mutual_reqs = []
                for j in range(n_nodes):
                    commod = assem_commods[j]
                    n_id = n_ids.next()
                    mutual_reqs.append((n_id, commod))
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
        p = self.params
        
        n_node_ucaps = {} # number of capacities per node
        # populate request params
        for g_id, multi_reqs in request.items():
            p.AddRequestGroup(g_id)
            p.req_qty[g_id] = self._req_qty(multi_reqs)
            n_constr = s.n_req_constr.sample()
            p.constr_vals[g_id] = self._req_constr_vals(n_constr, multi_reqs)
            excl_nodes = []
            for reqs in multi_reqs: # mutually satisfying requests
                for n_id, commod in reqs:
                    n_node_ucaps[n_id] = n_constr
                    p.AddRequestNode(n_id, g_id)
                    qty = self._req_node_qty()
                    p.node_qty[n_id] = qty
                    p.def_constr_coeff[n_id] = self._req_def_constr(qty)
                    excl = s.exclusive.sample() # exclusive or not
                    p.node_excl[n_id] = excl
                    if excl:
                        excl_nodes.append(n_id)
            p.excl_req_nodes[g_id] = excl_nodes
    
        # populate supply params and arc relations
        arcs = {} # arc: (request id, supply id)
        a_ids = Incrementer(self.arc_offset)
        commod_demand = self._commod_demand()
        supplier_capacity = \
            self._supplier_capacity(commod_demand, supplier_commods)
        for g_id, sups in supply.items():
            p.AddSupplyGroup(g_id)
            n_constr = s.n_sup_constr.sample()
            p.constr_vals[g_id] = \
                self._sup_constr_vals(supplier_capacity[g_id], n_constr)
            for s_id, r_id in sups:
                p.AddSupplyNode(s_id, g_id)
                n_node_ucaps[s_id] = n_constr
                arcs[a_ids.next()] = (r_id, s_id)

        # populate arc params
        for arc, ids in arcs.items():
            req, sup = ids
            p.arc_to_unode[arc] = req
            p.arc_to_vnode[arc] = sup
            p.node_ucaps[req][arc] = \
                [s.constr_coeff.sample() for i in range(n_node_ucaps[req])]
            p.node_ucaps[sup][arc] = \
                [s.constr_coeff.sample() for i in range(n_node_ucaps[sup])]
            p.arc_pref[arc] = s.pref_coeff.sample()

    def build(self, *args, **kwargs):
        """Returns a configured cyclopts.execute.GraphParams.
        """
        commods = self.commods
        requesters = self.requesters
        suppliers = self.suppliers

        request = self.generate_request(commods, requesters)
        supply, supplier_commods = self.generate_supply(commods, suppliers)

        requested_commods = set(v for k, v in self.reqs_to_commods.items())
        supplied_commods = set(v for k, v in self.sups_to_commods.items())
        if (requested_commods != set(commods)):
            raise ValueError("All commmodities are not requested.")
        if (supplied_commods != set(commods)):
            raise ValueError("All commmodities are not supplied.")
        self.populate_params(request, supply, supplier_commods)

        return self.params
    
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
        n_ids = self.sup_n_ids = Incrementer(self.req_n_offset + 
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

    def _req_qty(self, reqs):
        """Returns the request quantity for a request group.

        Parameters
        ----------
        reqs : list
            the requests associated with the group
        """
        # assumes 1 assembly == 1 mass unit, all constr vals equivalent. note
        # that reqs = [ [satisfying commods] ], so one entry per actual request
        return len(reqs)

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
        return [constr_val for i in range(n_constr)]
    
    def _req_node_qty(self):
        """Returns the quantity for an individual request."""
        # change these if all assemblies have mass != 1
        return 1
    
    def _req_def_constr(self, req_qty):
        """Returns the default constraint value for a request.

        Parameters
        ----------
        req_qty : float
            the request quantity
        """
        # change these if all assemblies have mass != 1
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
        return {sup: max([commod_demand[c] for c in commods]) \
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
        return [s.sup_constr_val.sample() * capacity for i in range(n_constr)]
