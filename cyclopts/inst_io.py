"""This module provides tools for writing and reading cyclopts.instance objects
to and from HDF5 databases.

:author: Matthew Gidden
"""
import numpy as np
import tables as t
from collections import Iterable

import cyclopts.exchange_instance as inst

_N_CAPS_MAX = 10

# add to this if more objects need to be persistable
_in_tbl_names = {
    "ExGroup": "ExchangeGroups",
    "ExNode": "ExchangeNodes",
    "ExArc": "ExchangeArcs",
    "properties": "ExchangeInstProperties",
    }
_out_tbl_names = {
    "solutions": "ExchangeInstSolutions",
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
    "properties": np.dtype([
        ("paramid", ('str', 16)), # 16 bytes for uuid
        ("instid", ('str', 16)), # 16 bytes for uuid
        ("n_arcs", np.int64),
        ("n_u_grps", np.int64),
        ("n_v_grps", np.int64),
        ("n_u_nodes", np.int64),
        ("n_v_nodes", np.int64),
        ("n_constrs", np.int64),
        ("excl_frac", np.float64),
        ]),
    "solutions": np.dtype([
        ("solnid", ('str', 16)), # 16 bytes for uuid
        ("instid", ('str', 16)), # 16 bytes for uuid
        ("arc_id", np.int64),
        ("flow", np.float64),
        ]),
    }

# these functions must be kept up to date with cyclopts.instance
def exgroup_tpl(idbytes, obj):    
    return(idbytes, obj.id, obj.kind, 
           np.append(obj.caps, [0] * (_N_CAPS_MAX - len(obj.caps))), obj.qty)

def exnode_tpl(idbytes, obj):    
    return(idbytes, obj.id, obj.gid, obj.kind, obj.qty, obj.excl, obj.excl_id)

def exarc_tpl(idbytes, obj):    
    return(idbytes, obj.id, 
           obj.uid, np.append(obj.ucaps, [0] * (_N_CAPS_MAX - len(obj.ucaps))), 
           obj.vid, np.append(obj.vcaps, [0] * (_N_CAPS_MAX - len(obj.vcaps))), 
           obj.pref)

_tpl_funcs = {'ExGroup': exgroup_tpl, 'ExNode': exnode_tpl, 'ExArc': exarc_tpl, }
    
_filters = t.Filters(complevel=4)

"""returns a list of object members that do not start with '_' or '__'. This is
specifically useful for listing the variables of an xdressed object.
"""
def xdvars(obj):
    return [x for x in obj.__class__.__dict__.keys() if not x.startswith('_')]
    
"""Checks if a file has known Exchange-related tables and adds them if not"""
def check_extables(h5node, names=_in_tbl_names):
    for objname, tname in names.items():
        if tname in h5node._v_children:
            continue
        h5node._v_file.create_table(h5node, tname, _dtypes[objname], 
                                    filters=_filters)

def write_exobjs(h5node, idbytes, objs):
    cname = objs[0].__class__.__name__
    dt = _dtypes[cname]
    names = dt.names[1:] # instid is first and not a attr
    rows = np.empty(len(objs), dtype=dt)
    tpl_func = _tpl_funcs[cname]
    for i in range(len(objs)):
        rows[i] = tpl_func(idbytes, objs[i])
    tname = _in_tbl_names[cname]
    tbl = getattr(h5node, tname)
    tbl.append(rows)
    tbl.flush()

def write_exprops(h5node, idbytes, paramid, groups, nodes, arcs):
    tbl = getattr(h5node, _in_tbl_names['properties'])
    row = tbl.row
    row['instid'] = idbytes
    row['paramid'] = paramid.bytes
    row['n_arcs'] = len(arcs)
    excl = {n.id: n.excl for n in nodes}
    nexcl = sum([int(excl[a.uid] or excl[a.vid]) for a in arcs])
    row['excl_frac'] = nexcl / float(len(arcs))
    nconstr = 0
    nv = 0
    nu = 0
    for g in groups:
        if g.kind:
            nu += 1
        else:
            nv += 1
        nconstr += len(g.caps)
    row['n_constrs'] = nconstr
    row['n_u_grps'] = nu
    row['n_v_grps'] = nv
    nv = 0
    nu = 0
    for n in nodes:
        if n.kind:
            nu += 1
        else:
            nv += 1
    row['n_u_nodes'] = nu
    row['n_v_nodes'] = nv
    row.append()
    tbl.flush()

def write_exinst(h5node, instid, paramid, groups, nodes, arcs):
    idbytes = instid.bytes
    check_extables(h5node, _in_tbl_names)
    write_exobjs(h5node, idbytes, groups)
    write_exobjs(h5node, idbytes, nodes)
    write_exobjs(h5node, idbytes, arcs)
    write_exprops(h5node, idbytes, paramid, groups, nodes, arcs)

def read_exobjs(h5node, instid, ctor):
    inst = ctor()
    cname = inst.__class__.__name__
    tname = _in_tbl_names[cname]
    objs = []
    tbl = getattr(h5node, tname)
    findid = instid
    rows = tbl.where('instid == findid')
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

def read_exinst(h5node, instid):
    groups = read_exobjs(h5node, instid, inst.ExGroup)
    nodes = read_exobjs(h5node, instid, inst.ExNode)
    arcs = read_exobjs(h5node, instid, inst.ExArc)
    return groups, nodes, arcs

def write_soln(h5node, instid, soln, solnid):
    check_extables(h5node, _out_tbl_names)
    tname = _out_tbl_names['solutions'] 
    tbl = h5node._f_get_child(tname)
    row = tbl.row
    for id, flow in soln.flows.iteritems():
        if not flow > 0:
            continue
        row['solnid'] = solnid
        row['instid'] = instid
        row['arc_id'] = id
        row['flow'] = flow
        row.append()
    tbl.flush()
