"""This module defines a series of objects that represent entities that can be
composed into a representation of a parameter space.

:author: Matthew Gidden <matthew.gidden _at_ gmail.com>
"""

import random as rnd
import numpy as np
import copy as cp
import re
import collections
import uuid

class Param(object):
    """A class to sample events.
    """
    def __init__(self, avg, dist = None):
        """Parameters
        ----------
        avg : float
            average value
        dist : str
            string representation of a distribution
        """
        self.avg = avg
        self.dist = dist

    def init(self):
        pass

    def sample(self):
        """Return a value sampled from the distribution"""
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
PARAM_CTOR_ARGS = {
    Param: ['avg', 'dist'],
    BoolParam: ['cutoff', 'dist'],
    CoeffParam: ['lb', 'ub', 'dist'],
    SupConstrParam: ['cutoff', 'rand', 'fracs'],
}
