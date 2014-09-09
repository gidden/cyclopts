import math
import numpy as np
from collections import namedtuple

from cyclopts.structured_species import data

"""default values and np.dtypes for points making up parameter space"""
Param = namedtuple('Param', ['val', 'dtype'])

class Point(object):
    """A container class representing a point in parameter space"""
    
    def __init__(self, d=None):
        """Parameters
        ----------
        d : dict, optional
            a dictionary with key value pairs of parameter name, parameter 
            value
        """
        d = d if d is not None else {}
        # init with dict-specified value else default
        for name, param in self._parameters().items():
            val = d[name] if name in d else param.val
            setattr(self, name, val)
        
    def _parameters(self):
        """subclasses must implement their parameter mapping"""
        return NotImplemented

    def __eq__(self, other):
        return (isinstance(other, self.__class__) \
                    and self.__dict__ == other.__dict__)

    def __ne__(self, other):
        return not self.__eq__(other)


def conv_ratio(kind):
    """provides the inventory to process conversion ratio for given support"""
    commod, rxtr = data.sup_to_commod[kind], data.sup_to_rxtr[kind]
    mean_enr = np.mean(data.enr_ranges[rxtr][commod])
    return data.converters[kind]['inv'](1.0, mean_enr, commod) / \
        data.converters[kind]['proc'](1.0, mean_enr, commod)

def region(loc, n_reg=1):
    """assumes loc is on [0, 1]"""
    return int(math.floor(n_reg * loc))

def preference(base_pref, r_loc, s_loc, loc_fidelity=0, ratio=1., n_reg=1):
    """returns the preference between a requester and supplier for a commodity"""
    commod_pref = base_pref
    loc_pref = 0

    if loc_fidelity > 0: # at least coarse
        rreg = region(r_loc, n_reg=n_reg)
        sreg = region(s_loc, n_reg=n_reg)
        loc_pref = math.exp(-np.abs(rreg - sreg))
    
    if loc_fidelity > 1: # fine
        loc_pref = (loc_pref + math.exp(-np.abs(r_loc - s_loc))) / 2

    return commod_pref + ratio * loc_pref
