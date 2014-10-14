import math
import numpy as np
from collections import namedtuple
import random

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

def mean_enr(rxtr, commod):
    """the mean enrichment for a reactor and commodity"""
    return np.mean(data.enr_ranges[rxtr][commod])

def conv_ratio(kind):
    """provides the inventory to process conversion ratio for given support"""
    commod, rxtr = data.sup_to_commod[kind], data.sup_to_rxtr[kind]
    enr = mean_enr(rxtr, commod)
    return data.converters[kind]['inv'](1.0, enr, commod) / \
        data.converters[kind]['proc'](1.0, enr, commod)

def region(loc, n_reg=1):
    """assumes loc is on [0, 1]"""
    return int(math.floor(n_reg * loc))

def loc_pref(r_loc, s_loc, loc_fidelity=0, n_reg=1):
    """returns the location-based preference between a requester and supplier
    for a commodity"""
    loc_pref = 0

    if loc_fidelity > 0: # at least coarse
        rreg = region(r_loc, n_reg=n_reg)
        sreg = region(s_loc, n_reg=n_reg)
        loc_pref = math.exp(-np.abs(rreg - sreg))
    
    if loc_fidelity > 1: # fine
        loc_pref = (loc_pref + math.exp(-np.abs(r_loc - s_loc))) / 2

    return loc_pref

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

def assembly_roulette(fracs):
    """In the case where this is only one assembly (i.e., low reactor fidelity),
    this method chooses the index
    
    Parameters
    ----------
    fracs : list
        the assembly distribution, assumed to be normalized

    Returns
    -------
    idx : int
        the chosen list index
    """
    rnd = random.uniform(0, 1)
    cum_sum = 0
    for i in range(len(fracs)):
        cum_sum += fracs[i]
        if rnd <= cum_sum:
            return i

def assembly_breakdown(point, kind):
    """Returns
    -------
    assems : dict
        a dictionary from commodity types to the number of assemblies
    """
    if kind == data.Reactors.th:
        fracs = point.d_th
    elif kind == data.Reactors.f_mox:
        fracs = point.d_f_mox
    elif kind == data.Reactors.f_thox:
        fracs = point.d_f_thox
    denom = float(sum(fracs))
    fracs = [x / denom for x in fracs]

    if point.f_rxtr == 0: # one 'assembly', i.e. a batch 
        ret = [0] * len(fracs)
        ret[assembly_roulette(fracs)] = 1
    else: # full assemblies
        nassems = data.n_assemblies[kind]
        ret = [int(round(x * nassems)) for x in fracs]
        
        diff = sum(ret) - nassems
        if diff != 0: # adjust largest amount to give exactly nassems
            ret[ret.index(max(ret))] -= diff
    return {data.Commodities[i]: ret[i] for i in range(len(ret))}
    
class Reactor(object):
    """A simplified reactor model for Structured Species"""

    def __init__(self, kind, point=None, n_assems=None):
        self.kind = kind
        if point is not None:
            self.n_assems = 1 if point.f_rxtr == 0 else data.n_assemblies[kind]
        elif n_assems is not None:
            self.n_assems = n_assems
        self.enr_rnd = random.uniform(0, 1) 
        self.loc = data.loc()

    def enr(self, commod):
        # node quantity takes into account relative fissile material
        lb, ub = data.enr_ranges[self.kind][commod]
        return (ub - lb) * self.enr_rnd + lb

    def coeffs(self, commod):
        return [1 / data.relative_qtys[self.kind][commod]]

"""Structured Arc Table Members"""
arc_tbl_name = "Arcs"
arc_tbl_dtype = np.dtype(
    [('instid', ('str', 16)), ('arcid', np.uint32), ('commod', np.uint32), 
     ('pref_c', np.float32), ('pref_l', np.float32)])
"""Structured Post-Processing Table Members"""
pp_tbl_name = "PostProcess"
pp_tbl_dtype = np.dtype(
    [('solnid', ('str', 16)), ('c_pref_flow', np.float64), 
     ('l_pref_flow', np.float64)])

def _iid_to_prefs(iid, tbl, narcs):
    """return a numpy array of preferences"""
    c_ret = np.zeros(narcs)
    l_ret = np.zeros(narcs)
    aid = 42
    for x in tbl.uuid_rows(iid):
        aid = x['arcid']
        c_ret[aid] = x['pref_c']
        l_ret[aid] = x['pref_l']
    return c_ret, l_ret

def post_process(instid, solnids, props, tbls):
    """Perform any post processing on input and output.
    
    Parameters
    ----------
    instid : UUID 
        UUID of the instance to post process
    solnids : tuple of UUIDs
        a collection of solution UUIDs corresponding the instid 
    props : tuple, other
        as defined by cyclopts.exchange_family 
    tbls : tuple of cyclopts.cyclopts_io.Tables
        tables from an input file, tables from an output file,
        and tables from a post-processed file
    """
    intbls, outtbls, pptbls = tbls
    narcs, sid_to_flows = props
    arc_tbl = intbls[arc_tbl_name]
    pp_tbl = pptbls[pp_tbl_name]
    
    c_prefs, l_prefs = _iid_to_prefs(instid, arc_tbl, narcs)
    data = []
    for sid, flows in sid_to_flows.items():
        c_pref_flow = np.dot(c_prefs, flows)
        l_pref_flow = np.dot(l_prefs, flows)
        data.append((sid.bytes, c_pref_flow, l_pref_flow))
    pp_tbl.append_data(data)
