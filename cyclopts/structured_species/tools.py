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

def reactor_breakdown(point):
    """Returns
    -------
    n_uox, n_mox, n_thox : tuple
    the number of each reactor type
    """
    n_rxtr = point.n_rxtr
    fidelity = point.f_fc
    r_t_f = point.r_t_f # thermal to fast
    r_th_pu = point.r_th_pu # thox to mox
    n_uox, n_mox, n_thox = 0, 0, 0
    if fidelity == 0: # once through
        n_uox = max(n_rxtr, 1)
    elif fidelity == 1: # uox + fast mox
        n_uox = max(int(round(r_t_f * n_rxtr)), 1)
        n_mox = max(n_rxtr - n_uox, 1)
    else: # uox + fast mox + fast thox
        n_uox = max(int(round(r_t_f * n_rxtr)), 1)
        n_thox = max(int(round(r_th_pu * (n_rxtr - n_uox))), 1)
        n_mox = max(n_rxtr - n_uox - n_thox, 1)
    return n_uox, n_mox, n_thox

def support_breakdown(point):
    """Returns
    -------
    n_uox, n_mox, n_thox, n_repo : tuple
    the number of each support type
    """
    n_uox_r, n_mox_r, n_thox_r = reactor_breakdown(point)
    n_uox, n_t_mox, n_f_mox, n_f_thox, n_repo = 0, 0, 0, 0, 0
    fidelity = point.f_fc

    # number thermal supports
    if fidelity == 0: # once through - only uox
        n_uox = max(int(round(point.r_s_th * n_uox_r)), 1)
    else:
        n_s_t = max(int(round(point.r_s_th * n_uox_r)), 1)
        n_uox = max(int(round(n_s_t / (1.0 + point.r_s_mox_uox))), 1)
        n_t_mox = max(n_s_t - n_uox, 1)
        
    # number f_mox supports
    if fidelity > 0:
        n_f_mox = max(int(round(point.r_s_mox * n_mox_r)), 1)
            
    # number f_thox supports
    if fidelity > 1:
        n_f_thox = max(int(round(point.r_s_thox * n_thox_r)), 1)
 
    if hasattr(point, 'r_repo'):
        n_repo = max(int(round(sum([n_uox, n_t_mox, n_f_mox, n_f_thox]) * \
                                   point.r_repo)), 1)

    return n_uox, n_t_mox, n_f_mox, n_f_thox, n_repo

def assembly_breakdown(point):
    """Returns
    -------
    n_uox, n_th_mox, n_f_mox, n_f_thox : tuple
    the number of each assembly type for a reactor
    """
    
