"""Implements a robust interface for translating scaling parameters into a full
parameter definition of a resource exchange graph in Cyclus.

:author: Matthew Gidden <matthew.gidden@gmail.com>
"""

import random as rnd
import numpy as np

from execute import ExecParams

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
    def __init__(self, avg, dist = None, *args, **kwargs):
        self.avg = avg
        self.dist = dist

    def sample(self):
        # if self.dist is None:
        #     return self.avg
        return self.avg

class BoolParam(object):
    """A class to sample binary events
    """
    def __init__(self, cutoff, dist = None, *args, **kwargs):
        """Parameters
        ----------
        cutoff : float
            the probability cutoff
        """
        self.cutoff = cutoff
        self.dist = dist

    def sample(self):
        """Returns True if sampled below the cutoff, False otherwise"""
        # if self.dist is None:
        #     return self.avg
        return self.cutoff >= rnd.uniform(0, 1)

class CoeffParam(object):
    """A class to sample coefficient values
    """
    def __init__(self, lb = 0, ub = 1, dist = None, *args, **kwargs):
        """Parameters
        ----------
        lb : float
            the coefficient lower bound
        ub : float
            the coefficient upper bound
        dist : a distribution from the random module
            the distribution to use, default is uniform
        """
        self.lb = lb
        self.ub = ub
        self.dist = dist if dist is not None else rnd.uniform

    def sample(self):
        """Returns a sampled coefficient"""
        return self.dist(self.lb, self.ub)

class SupConstrParam(object):
    """A base class for sampled supply constraint values.
    """
    def __init__(self, cutoff, dist = False, fracs = None, *args, **kwargs):
        """Parameters
        ----------
        cutoff : float
            the lowest supply fraction
        dist : bool
            if True, a random supply fraction greater than or equal to the 
            cutoff is provided during sampling; if False, the cutoff fraction 
            is used
        fracs : list
            a collection of fractional values of commodity demand that the 
            supply constraint value could take; default is [0.25, 0.5, 0.75, 1]
        """
        self.cutoff = cutoff
        self.dist = dist
        # possible supply fractions
        fracs = fracs if fracs is not None else [0.25, 0.5, 0.75, 1] 
        self.fracs = [frac for frac in fracs if frac >= cutoff]

    def sample(self):
        """Returns a fractional supply constraint value for a commodity"""
        if self.dist:
            return self.cutoff
        else:
            return rnd.choice(self.fracs)

class ReactorRequestSampler(object):
    """A container class for holding all sampling objects for reactor request
    scenarios.
    """
    def __init__(self, n_commods = None, 
                 n_request = None, assem_per_req = None, req_multi_frac = None, 
                 req_multi_commods = None, exclusive = None, n_req_constr = None, 
                 n_supply = None, sup_multi_frac = None, sup_multi_commods = None, 
                 n_sup_constr = None, sup_constr_val = None, 
                 connection = None, constr_coeff = None, pref_coeff = None,
                 *args, **kwargs):
        """Parameters
        ----------
        n_commods : Param or similar, optional
            the number of commodities
        n_request : Param or similar, optional
            the number of requesters (i.e., RequestGroups)
        assem_per_req : Param or similar, optional
            the number of assemblies in a request
        req_multi_frac : Param or similar, optional
            the fraction of assemblies that can be satisfied by multiple 
            commodities (the multicommodity zone)
        req_multi_commods : Param or similar, optional
            the number of commodities in a multicommodity zone
        exclusive : BoolParam or similar, optional
            the probability that a reactor assembly request is exclusive
        n_req_constr : Param or similar, optional
            the number of constraints associated with a given request group
        n_supply : Param or similar, optional
            the number of suppliers (i.e., supply ExchangeNodeGroups)
        sup_multi_frac : Param or similar, optional
            the fraction of suppliers that supply more than one commodity
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
        self.req_multi_frac = req_multi_frac \
            if req_multi_frac is not None else Param(0)
        self.req_multi_commods = req_multi_commods \
            if req_multi_commods is not None else Param(1)
        self.exclusive = exclusive \
            if exclusive is not None else BoolParam(-1) # never true
        self.n_req_constr = n_req_constr \
            if n_req_constr is not None else Param(0)
        self.n_supply = n_supply \
            if n_supply is not None else Param(1)
        self.sup_multi_frac = sup_multi_frac \
            if sup_multi_frac is not None else Param(0)
        self.sup_multi_commods = sup_multi_commods \
            if sup_multi_commods is not None else Param(1)
        self.n_sup_constr = n_sup_constr \
            if n_sup_constr is not None else Param(1)
        self.sup_constr_val = sup_constr_val \
            if sup_constr_val is not None else SupConstrParam(1)
        self.connection = connection \
            if connection is not None else BoolParam(1)
        self.constr_coeff = constr_coeff \
            if constr_coeff is not None else CoeffParam(np.nextafter(0, 1), 1)
        self.pref_coeff = pref_coeff \
            if pref_coeff is not None else CoeffParam(np.nextafter(0, 1), 1)

class ReactorRequestParams(object):
    """A helper class to translate sampling parameters for a reactor request
    scenario into an instance of ExecParams used by the cyclopts.execute
    module.

    params is populated by the various generate_* functions.
    """
    def __init__(self, sampler, commod_offset = 0, req_g_offset = 0, 
                 sup_g_offset = 0, req_n_offset = 0, sup_n_offset = 0, 
                 *args, **kwargs):
        """Parameters
        ----------
        sampler : ReactorRequestSampler
            a parameter sampling container
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
        """
        self.sampler = sampler
        self.commod_offset = commod_offset
        self.req_g_ids = Incrementer(req_g_offset)
        self.sup_g_ids = Incrementer(sup_g_offset)
        self.req_n_ids = Incrementer(req_n_offset)
        self.sup_n_ids = Incrementer(sup_n_offset)
        self.params = ExecParams()
    
    def generate_request(self, commods, n_request, *args, **kwargs):
        """Generates supply-related parameters.

        Parameters
        ----------
        commods : set
            the commodities
        n_request : int
            the number of requesters        
        """
        for i in range(len(n_request)):
            g_id = self.req_g_ids.next()
            
    
    def generate_supply(self, commods, n_supply, *args, **kwargs):
        """Generates supply-related parameters.

        Parameters
        ----------
        commods : list
        a list of the commodities
        n_supply : int
        the number of suppliers
        
        
        """
        pass
    
    def generate_arcs(self, *args, **kwargs):
        """Generates arcs between suppliers and requesters.
        """
        pass
    
    def generate_coeffs(self, *args, **kwargs):
        """Generates constraint and preference coefficients.
        """
        pass

    def generate(self, *args, **kwargs):
        """Returns a configured cyclopts.execute.ExecParams after calling each
        generation member function in order.
        """
        commods = set(range(self.commod_offset, 
                            self.commod_offset + self.n_commods.sample()))
        n_request = self.n_request.sample()
        n_supply = self.n_supply.sample()

        self.generate_request(commods, n_request)
        self.generate_supply(commods, n_supply)
        self.generate_arcs()
        self.generate_coeffs()

        return self.params

class ReactorSupplyParams(object):
    """A helper class to translate sampling parameters for a reactor supply
    scenario into an instance of ExecParams used by the cyclopts.execute
    module.
    """
    def __init__(self, *args, **kwargs):
        """Parameters
        ----------
        n_commods : Param or similar, optional
            the number of commodities in the exchange
        """
        self.n_commods = n_commods
        self.n_supply = n_supply
        self.n_request = n_request
        self.assem_per_sup = assem_per_sup
        self.commod_per_sup = commod_per_sup
        self.assem_commod = assem_commod
        self.p_excl = p_excl
        self.p_connect = p_connect
        self.u_caps = u_caps
        self.prefs = prefs
        self.sup_constr_val = sup_constr_val
        self.sup_n_constr = sup_n_constr
        self.dem_constr_val = dem_constr_val
        self.dem_multi_frac = dem_multi_frac
        self.dem_n_multi = dem_n_multi
        self.dem_n_constr = dem_n_constr

    def get():
        """Returns a configured cyclopts.execute.ExecParams."""
        params = ExecParams()
        return params        
