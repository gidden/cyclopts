"""Implements a robust interface for translating scaling parameters into a full
parameter definition of a resource exchange graph in Cyclus.

:author: Matthew Gidden <matthew.gidden@gmail.com>
"""

from execute import ExecParams

class Param(object):
    """A base class for sampled parameters.
    """
    def __init__(self, avg, dist = None):
        self.avg = avg
        self.dist = dist

    def sample():
        # if self.dist is None:
        #     return self.avg
        return self.avg

class ReactorRequestParams(object):
    """A helper class to translate sampling parameters for a reactor request
    scenario into an instance of ExecParams used by the cyclopts.execute
    module.
    """
    def __init__(self, *args, **kwargs):
        """Parameters
        ----------
        param : Param or similar, optional
            some parameter
        """
        self.n_commods = n_commods
        self.n_supply = n_supply
        self.n_request = n_request

    def get():
        """Returns a configured cyclopts.execute.ExecParams."""
        params = ExecParams()
        return params

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
        self.assem_per_req = assem_per_req
        self.req_val = req_val
        self.dem_multi_frac = dem_multi_frac
        self.dem_n_multi = dem_n_multi
        self.p_excl = p_excl
        self.dem_n_constr = dem_n_constr
        self.dem_constr_val = dem_constr_val
        self.sup_multi_frac = sup_multi_frac
        self.n_request = sup_n_multi
        self.sup_constr_val = sup_constr_val
        self.u_caps = u_caps
        self.prefs = prefs
        self.p_connect = p_connect

    def get():
        """Returns a configured cyclopts.execute.ExecParams."""
        params = ExecParams()
        return params        
