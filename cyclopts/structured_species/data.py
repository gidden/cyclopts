"""Data for structured species"""
import random
from enum import Enum
import numpy as np
import math

import warnings
with warnings.catch_warnings():
    from pyne.utils import VnVWarning
    warnings.filterwarnings("ignore", category=VnVWarning)
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

class Supports(Enum):    
    uox = 1
    th_mox = 2
    f_mox = 3
    f_thox = 4
    repo = 5

commod_to_sup = {
    Commodities.uox: Supports.uox,
    Commodities.th_mox: Supports.th_mox,
    Commodities.f_mox: Supports.f_mox,
    Commodities.f_thox: Supports.f_thox,
}

sup_to_commod = {
    Supports.uox: Commodities.uox,
    Supports.th_mox: Commodities.th_mox,
    Supports.f_mox: Commodities.f_mox,
    Supports.f_thox: Commodities.f_thox,
}

sup_to_rxtr = {
    Supports.uox: Reactors.th,
    Supports.th_mox: Reactors.th,
    Supports.f_mox: Reactors.f_mox,
    Supports.f_thox: Reactors.f_thox,
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
        Commodities.th_mox : 0.07,
        Commodities.f_mox : 0.07,
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
rxtr_pref_basis = {
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

"""Initial preference values, functional shape can be changed based on
parameters in run control"""
sup_pref_basis = {
    Supports.th_mox : {
        Commodities.uox : 1.5,
        Commodities.th_mox : 1.0,
        Commodities.f_mox : 0.5,
        },
    Supports.f_mox : {
        Commodities.uox : 0.5,
        Commodities.th_mox : 0.5,
        Commodities.f_mox : 1.0,
        },
    Supports.f_thox : {
        Commodities.uox : 0.3,
        Commodities.f_thox : 1.0,
        },
    Supports.repo : {
        Commodities.uox : 0.01,
        Commodities.th_mox : 0.01,
        Commodities.f_mox : 0.01,
        Commodities.f_thox : 0.01,
        },
    }

"""support limiting values"""
sup_rhs = {
    Supports.uox: 3.3e6/12, # 3.3M SWU/yr / 12 months/yr
    Supports.th_mox: 800e3/12, # 800 t/yr / 12 months/yr
    Supports.f_mox: 800e3/12,
    Supports.f_thox: 800e3/12,
    Supports.repo: 575e3/12, # 575 t/yr / 12 months/yr
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
        return qty * enr / 100.

class RepoProc(Converter):
    def __call__(self, qty, enr, commod=None):
        return qty

converters = {
    Supports.uox: {
        'proc': SWU(), 
        'inv': NatU(),
        },
    Supports.th_mox: {
        'proc': RecycleProc(), 
        'inv': RecycleInv(),
        },
    Supports.f_mox: {
        'proc': RecycleProc(), 
        'inv': RecycleInv(),
        },
    Supports.f_thox: {
        'proc': RecycleProc(), 
        'inv': RecycleInv(),
        },
    Supports.repo: {
        'proc': RepoProc(), 
        },
}

"""generate a location"""
loc = lambda: random.uniform(0, 1)
