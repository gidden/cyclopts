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
