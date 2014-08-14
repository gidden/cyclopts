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

:author: Matthew Gidden <matthew.gidden _at_ gmail.com>
"""

import random as rnd
import numpy as np
import copy as cp
import re
import collections
import uuid

try:
    import cyclopts.exchange_instance as inst
    import cyclopts.inst_io as iio 
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

    def init(self):
        pass

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

    def init(self):
        pass

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
        self._dist_func = rnd.uniform # update this for more functions

    def init(self):
        self._dist_func = rnd.uniform # update this for more functions

    def sample(self):
        """Returns a sampled coefficient"""
        #if self.dist == "uniform":
        return self._dist_func(self.lb, self.ub)

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
        #self.fracs = [frac for frac in fracs if frac >= cutoff] if self.rand \
        #    else [cutoff]
        self.fracs = [frac for frac in fracs if frac >= cutoff]

    def init(self):
        pass

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
        n_ids = self.req_n_ids = Incrementer(self.req_n_offset)
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
            self.groups.append(inst.ExGroup(g_id, req, caps, total_grp_qty))
            
            exid = Incrementer()
            for reqs in multi_reqs: # mutually satisfying requests
                for n_id, commod in reqs:
                    n_node_ucaps[n_id] = n_constr
                    req_qty = self._req_node_qty()
                    excl = s.exclusive.sample() # exclusive or not
                    excl_id = exid.next() if excl else -1 # need unique exclusive id
                    self.nodes.append(
                        inst.ExNode(n_id, g_id, req, req_qty, excl, excl_id))
                    req_qtys[n_id] = req_qty
    
        # populate supply params and arc relations
        a_ids = Incrementer(self.arc_offset)
        commod_demand = self._commod_demand()
        supplier_capacity = \
            self._supplier_capacity(commod_demand, supplier_commods)
        for g_id, sups in supply.items():
            caps = self._sup_constr_vals(supplier_capacity[g_id], 
                                         s.n_sup_constr.sample())
            self.groups.append(inst.ExGroup(g_id, bid, caps))
            for v_id, u_id in sups:
                req_qty = req_qtys[u_id]
                n_node_ucaps[v_id] = len(caps)
                self.nodes.append(inst.ExNode(v_id, g_id, bid, req_qty))
                # arc from u-v node
                # add qty as first constraint -- required for clp/cbc
                ucaps = np.append(
                    [self._req_def_constr(req_qty)], 
                    [s.constr_coeff.sample() for i in range(n_node_ucaps[u_id])])
                vcaps = [s.constr_coeff.sample() for i in range(n_node_ucaps[v_id])]
                self.arcs.append(
                    inst.ExArc(a_ids.next(), u_id, ucaps, 
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

        req_g_ids = Incrementer(self.req_g_offset)
        # request groups
        requesters = self.requesters = \
            [req_g_ids.next() for i in range(self.n_request)] 
        # include request values because ids are global
        sup_g_ids = \
            Incrementer(self.req_g_offset + self.sup_g_offset + self.n_request)
        # supply groups
        suppliers = self.suppliers = \
            [sup_g_ids.next() for i in range(self.n_supply)] 
        self.arc_ids = Incrementer(self.arc_offset)

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

    def write(self, h5node):
        """writes its current instance state to an output database"""
        instid = uuid.uuid4()
        iio.write_exinst(h5node, instid, self.sampler.paramid, 
                         self.groups, self.nodes, self.arcs)
    
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
