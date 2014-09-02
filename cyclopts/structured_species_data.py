"""Data for structured species"""
import random
from enum import Enum
import numpy as np
import math
from pyne import enrichment

class Commodities(Enum):
    uox = 1
    th_mox = 2
    f_mox = 3
    f_thox = 4

class Reactors(Enum):    
    th = 1
    f_mox = 2
    f_thox = 3

class Suppliers(Enum):    
    uox = 1
    th_mox = 2
    f_mox = 3
    f_thox = 4

commod_to_sup = {
    Commodities.uox: Suppliers.uox,
    Commodities.th_mox: Suppliers.th_mox,
    Commodities.f_mox: Suppliers.f_mox,
    Commodities.f_thox: Suppliers.f_thox,
}

sup_to_commod = {
    Suppliers.uox: Commodities.uox,
    Suppliers.th_mox: Commodities.th_mox,
    Suppliers.f_mox: Commodities.f_mox,
    Suppliers.f_thox: Commodities.f_thox,
}

sup_to_rxtr = {
    Suppliers.uox: Reactors.th,
    Suppliers.th_mox: Reactors.th,
    Suppliers.f_mox: Reactors.f_mox,
    Suppliers.f_thox: Reactors.f_thox,
}


def rxtr_commods(kind, fidelity):
    """return a list of commodities per reactor kind and fidelity"""
    commods = [Commodities.uox]
    if fidelity > 0:
        commods += [Commodities.th_mox, Commodities.f_mox]
    if fidelity > 1 and kind != Reactors.th:
        commods += [Commodities.f_thox]
    return commods

"""lower bound, upper bound tuples of enrichment ranges"""
enr_ranges = {
    Reactors.th : {
        Commodities.uox : (3.5, 5.5),
        Commodities.th_mox : (55.0, 65.0),
        Commodities.f_mox : (55.0, 65.0),
        },
    Reactors.f_mox : {
        Commodities.uox : (15.0, 20.0),
        Commodities.th_mox : (55.0, 65.0),
        Commodities.f_mox : (55.0, 65.0),
        Commodities.f_thox : (55.0, 65.0),
        },
    Reactors.f_thox : {
        Commodities.uox : (15.0, 20.0),
        Commodities.th_mox : (55.0, 65.0),
        Commodities.f_mox : (55.0, 65.0),
        Commodities.f_thox : (55.0, 65.0),
        },
}

"""fuel unit in kgs"""
fuel_unit = 1400.0

"""fast reactor requests are unity, thermal reactors are larger by an active
core volume fraction"""
request_qtys = {
    Reactors.th : 12.5, 
    Reactors.f_mox : 1.0, 
    Reactors.f_thox : 1.0, 
}

"""total number of assemblies in a reactor core reload"""
reload_frac = 1./4
n_assemblies = {
    Reactors.th : int(math.floor(157 * reload_frac)), # ap-1000 style
    Reactors.f_mox : int(math.floor(369 * reload_frac)), # bn-600 style 
    Reactors.f_thox : int(math.floor(369 * reload_frac)), # bn-600 style
}

"""Relative quantity of fissile material required from supporting facilities --
COMMODITIES.UOX requests include U-238, MOX/COMMODITIES.F_THOX requests only include fissile material."""
relative_qtys = {
    Reactors.th : {
        Commodities.uox : 1.0,
        Commodities.th_mox : 0.1,
        Commodities.f_mox : 0.1,
        },
    Reactors.f_mox : {
        Commodities.uox : 1.0,
        Commodities.th_mox : 0.2,
        Commodities.f_mox : 0.2,
        Commodities.f_thox : 0.2,
        },
    Reactors.f_thox : {
        Commodities.uox : 1.0,
        Commodities.th_mox : 0.2,
        Commodities.f_mox : 0.2,
        Commodities.f_thox : 0.2,
        },
}

"""Initial preference values, functional shape can be changed based on
parameters in run control"""
pref_basis = {
    Reactors.th : {
        Commodities.uox : 0.5,
        Commodities.th_mox : 1.0,
        Commodities.f_mox : 0.1,
        },
    Reactors.f_mox : {
        Commodities.uox : 0.1,
        Commodities.th_mox : 0.5,
        Commodities.f_mox : 1.0,
        Commodities.f_thox : 0.25,
        },
    Reactors.f_thox : {
        Commodities.uox : 0.1,
        Commodities.th_mox : 0.25,
        Commodities.f_mox : 0.5,
        Commodities.f_thox : 1.0,
        },
    }

"""supplier limiting values"""
sup_rhs = {
    Suppliers.uox: 3.3e6/12, # 3.3M SWU/yr / 12 months/yr
    Suppliers.th_mox: 800e3/12, # 800t/yr / 12 months/yr
    Suppliers.f_mox: 800e3/12,
    Suppliers.f_thox: 800e3/12,
    }

class Converter(object):
    """pure virtual class for conversion functions"""
    def __call__(self, qty, enr, commod=None):
        """derived classes must return a value representing a constraint
        coefficient"""
        raise NotImplementedError

class NatU(Converter):
    def __call__(self, qty, enr, commod=None):
        return enrichment.feed(0.0072, enr / 100., 0.0025, product=qty)

class SWU(Converter):
    def __call__(self, qty, enr, commod=None):
        return enrichment.swu(0.0072, enr / 100., 0.0025, product=qty)

class RecycleProc(Converter):
    def __call__(self, qty, enr, commod=None):
        factor = 1 if commod == Commodities.uox else 100
        return qty * factor

class RecycleInv(Converter):
    def __call__(self, qty, enr, commod=None):
        return qty * enr

converters = {
    Suppliers.uox: {
        'proc': SWU(), 
        'inv': NatU(),
        },
    Suppliers.th_mox: {
        'proc': RecycleProc(), 
        'inv': RecycleInv(),
        },
    Suppliers.f_mox: {
        'proc': RecycleProc(), 
        'inv': RecycleInv(),
        },
    Suppliers.f_thox: {
        'proc': RecycleProc(), 
        'inv': RecycleInv(),
        },
}

def conv_ratio(kind):
    commod, rxtr = sup_to_commod[kind], sup_to_rxtr[kind]
    mean_enr = np.mean(enr_ranges[rxtr][commod])
    return converters[kind]['proc'](1.0, mean_enr, commod) / \
        converters[kind]['inv'](1.0, mean_enr, commod)

"""generate a location"""
loc = lambda: random.uniform(0, 1)
