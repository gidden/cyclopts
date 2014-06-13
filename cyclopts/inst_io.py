"""This module provides tools for writing and reading cyclopts.instance objects
to and from HDF5 databases.

:author: Matthew Gidden
"""
import numpy as np
import tables as t

from cyclopts.instance import ExGroup, ExNode, ExArc 

_N_CAPS_MAX = 10
_tbl_names = {
    "ExGroup": "ExchangeGroups",
    "ExNode": "ExchangeNodes",
    "ExArc": "ExchangeArcs",
    }
_filters = t.Filters(complevel=4)

"""returns a list of object members that do not start with '_' or '__'. This is
specifically useful for listing the variables of an xdressed object.
"""
def xdvars(obj):
    return [attr for attr in dir(obj) \
                if not callable(attr) \
                and not attr.startswith('__') and not attr.startswith('_')]

def write_exgroups(h5node, instid, groups):
    name = _tbl_names["ExGroup"]
    if not name in h5node._v_children:
        # this must be kept up to date with the cyclopts.instance classes
        dtype = {
            "id": np.intc,
            "kind": np.bool_,
            "caps": np.dtype((np.float64, (_N_CAPS_MAX,))), # array of size N_CAPS_MAX
            "qty": np.float64,
            }
        h5file.create_table(h5node, name, dtype, filters=_filters)
    row = h5node.name.row
    for g in groups:
        row['instid'] = instid
        for var in xdvars(g):
            row[var] = getattr(g, var)
        row.append()

def read_exgroups(h5node, instid):
    name = _tbl_names["ExGroup"]
    groups = []
    rows = h5node.name.where("""instid == instid""")
    for row in rows:
        g = ExGroup()
        for var in xdvars(g):
            setattr(g, var, row[var])
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
