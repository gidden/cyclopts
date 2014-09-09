import math
import numpy as np

from cyclopts.structured_species import data

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
