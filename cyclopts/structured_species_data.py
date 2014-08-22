"""This module defines static data used in the structured request and supply
species.

:author: Matthew Gidden <matthew.gidden _at_ gmail.com>
"""

uox = "UOX"
tmox = "MOX_TH"
fmox = "MOX_F"
thox = "THOX"
commodities = [uox, tmox, fmox, thox]

r_t = "THERMAL"
r_mox = "FAST MOX"
r_thox = "FAST THOX"
reactors = [r_t, r_mox, r_thox]

"""lower bound, upper bound tuples of enrichment ranges"""
enrichment_ranges = {
    r_t : {
        uox : (3.5, 5.5),
        tmox : (55.0, 65.0),
        fmox : (55.0, 65.0),
        },
    r_mox : {
        uox : (15.0, 20.0),
        tmox : (55.0, 65.0),
        fmox : (55.0, 65.0),
        thox : (55.0, 65.0),
        },
    r_thox : {
        uox : (15.0, 20.0),
        tmox : (55.0, 65.0),
        fmox : (55.0, 65.0),
        thox : (55.0, 65.0),
        },
}

"""fast reactor requests are unity, thermal reactors are larger by an active
core volume fraction"""
request_qtys = {
    r_t : 12.5, 
    r_mox : 1.0, 
    r_thox : 1.0, 
}

"""Relative quantity of fissile material required from supporting facilities --
UOX requests include U-238, MOX/THOX requests only include fissile material."""
relative_qtys = {
    r_t : {
        uox : 1.0,
        tmox : 0.1,
        fmox : 0.1,
        },
    r_mox : {
        uox : 1.0,
        tmox : 0.2,
        fmox : 0.2,
        thox : 0.2,
        },
    r_thox : {
        uox : 1.0,
        tmox : 0.2,
        fmox : 0.2,
        thox : 0.2,
        },
}

"""Initial preference values, functional shape can be changed based on
parameters in run control"""
pref_basis = {
    r_t : {
        uox : 0.5,
        tmox : 1.0,
        fmox : 0.1,
        },
    r_mox : {
        uox : 0.1,
        tmox : 0.5,
        fmox : 1.0,
        thox : 0.25,
        },
    r_thox : {
        uox : 0.1,
        tmox : 0.25,
        fmox : 0.5,
        thox : 1.0,
        },
}
