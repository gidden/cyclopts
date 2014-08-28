"""Data for structured species"""

from enum import Enum

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

commodities_to_suppliers = {
    Commodities.uox: Suppliers.uox,
    Commodities.th_mox: Suppliers.th_mox,
    Commodities.f_mox: Suppliers.f_mox,
    Commodities.f_thox: Suppliers.f_thox,
}

"""lower bound, upper bound tuples of enrichment ranges"""
enrichment_ranges = {
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
