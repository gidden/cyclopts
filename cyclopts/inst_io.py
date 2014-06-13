"""This module provides tools for writing and reading cyclopts.instance objects
to and from HDF5 databases.

:author: Matthew Gidden
"""
import numpy as np
import tables as t
from collections import Iterable

from cyclopts.instance import ExGroup, ExNode, ExArc 

_N_CAPS_MAX = 10
_tbl_names = {
    "ExGroup": "ExchangeGroups",
    "ExNode": "ExchangeNodes",
    "ExArc": "ExchangeArcs",
    }
_filters = t.Filters(complevel=4)

# this must be kept up to date with the cyclopts.instance classes
_dtypes = {
    "ExGroup": np.dtype([
        ("instid", ('str', 16)), # 16 bytes for uuid
        ("id", np.int64),
        ("kind", np.bool_),
        ("caps", (np.float64, _N_CAPS_MAX),), # array of size N_CAPS_MAX
        ("qty", np.float64),
        ]),
    "ExNode": {
        "instit": np.dtype((np.void, 16)), # 16 bytes for uuid
        "id": np.int64,
        },
    "ExArc": {
        "instit": np.dtype((np.void, 16)), # 16 bytes for uuid
        "id": np.int64,
        },
    }

"""returns a list of object members that do not start with '_' or '__'. This is
specifically useful for listing the variables of an xdressed object.
"""
def xdvars(obj):
    return [attr for attr in dir(obj) \
                if not callable(attr) \
                and not attr.startswith('__') and not attr.startswith('_')]

"""Checks if a file has known Exchange-related tables and adds them if not"""
def check_extables(h5file, h5node):
    names = {"ExGroup": "ExchangeGroups"}
    for obj, name in names.items():#_tbl_names.items():
        if not name in h5node._v_children:
            h5file.create_table(h5node, name, _dtypes[obj], filters=_filters)

def write_exgroups(h5node, instid, groups):
    name = _tbl_names["ExGroup"]
    tbl = getattr(h5node, name)
    row = tbl.row
    for g in groups:
        row['instid'] = instid.bytes
        for var in xdvars(g):
            attr = getattr(g, var)
            if isinstance(attr, Iterable):
                zeros = [0] * (_N_CAPS_MAX - len(attr))
                attr = np.append(attr, zeros) # up the array to len 10 with 0 values
            row[var] = attr
        row.append()
    tbl.flush()

def read_exgroups(h5node, instid):
    name = _tbl_names["ExGroup"]
    groups = []
    tbl = getattr(h5node, name)
    byteid = instid.bytes
    rows = tbl.where('instid == byteid')
    for row in rows:
        g = ExGroup()
        for var in xdvars(g):
            attr = getattr(g, var)
            if isinstance(attr, Iterable):
                ary = row[var]
                attr = ary[ary > 0] 
            else:
                attr = row[var]
            setattr(g, var, attr)
        groups.append(g)
    return groups

def write_exnodes(h5node, instid, nodes):
    pass

def read_exnodes(h5node):
    pass

def write_exarcs(h5node, instid, arcs):
    pass

def read_exarcs(h5node):
    pass
