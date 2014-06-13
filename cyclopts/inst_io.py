"""This module provides tools for writing and reading cyclopts.instance objects
to and from HDF5 databases.

:author: Matthew Gidden
"""
import numpy as np
import tables as t
from collections import Iterable

_N_CAPS_MAX = 10

# add to this if more objects need to be persistable
_tbl_names = {
    "ExGroup": "ExchangeGroups",
    "ExNode": "ExchangeNodes",
    "ExArc": "ExchangeArcs",
    }

# this must be kept up to date with the cyclopts.instance classes
_dtypes = {
    "ExGroup": np.dtype([
        ("instid", ('str', 16)), # 16 bytes for uuid
        ("id", np.int64),
        ("kind", np.bool_),
        ("caps", (np.float64, _N_CAPS_MAX),), # array of size N_CAPS_MAX
        ("qty", np.float64),
        ]),
    "ExNode": np.dtype([
        ("instid", ('str', 16)), # 16 bytes for uuid
        ("id", np.int64),
        ("gid", np.int64),
        ("kind", np.bool_),
        ("qty", np.float64),
        ("excl", np.bool_),
        ("excl_id", np.int64),
        ]),
    "ExArc": np.dtype([
        ("instid", ('str', 16)), # 16 bytes for uuid
        ("id", np.int64),
        ("uid", np.int64),
        ("ucaps", (np.float64, _N_CAPS_MAX),), # array of size N_CAPS_MAX
        ("vid", np.int64),
        ("vcaps", (np.float64, _N_CAPS_MAX),), # array of size N_CAPS_MAX
        ("pref", np.float64),
        ]),
    }

_filters = t.Filters(complevel=4)

"""returns a list of object members that do not start with '_' or '__'. This is
specifically useful for listing the variables of an xdressed object.
"""
def xdvars(obj):
    return [attr for attr in dir(obj) \
                if not callable(attr) \
                and not attr.startswith('__') and not attr.startswith('_')]

"""Checks if a file has known Exchange-related tables and adds them if not"""
def check_extables(h5file, h5node):
    for objname, tname in _tbl_names.items():
        if tname in h5node._v_children:
            pass
        h5file.create_table(h5node, tname, _dtypes[objname], filters=_filters)

def write_exobjs(h5node, instid, objs):
    cname = objs[0].__class__.__name__
    tname = _tbl_names[cname]
    tbl = getattr(h5node, tname)
    row = tbl.row
    for obj in objs:
        row['instid'] = instid.bytes
        for var in xdvars(obj):
            attr = getattr(obj, var)
            if isinstance(attr, Iterable):
                zeros = [0] * (_N_CAPS_MAX - len(attr))
                attr = np.append(attr, zeros) # up the array to len 10 with 0 values
            row[var] = attr
        row.append()
    tbl.flush()

def read_exobjs(h5node, instid, ctor):
    inst = ctor()
    cname = inst.__class__.__name__
    tname = _tbl_names[cname]
    objs = []
    tbl = getattr(h5node, tname)
    byteid = instid.bytes
    rows = tbl.where('instid == byteid')
    vars = xdvars(inst)
    for row in rows:
        obj = ctor()
        for var in vars:
            attr = getattr(obj, var)
            if isinstance(attr, Iterable):
                ary = row[var]
                attr = ary[ary > 0] 
            else:
                attr = row[var]
            setattr(obj, var, attr)
        objs.append(obj)
    return objs