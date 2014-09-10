from cyclopts.structured_species import request as spmod

import uuid
import math
import os

from nose.tools import assert_equal, assert_almost_equal, assert_true, assert_false
from numpy.testing import assert_array_almost_equal

from cyclopts import tools as cyctools
from cyclopts.exchange_family import ResourceExchange
from cyclopts.structured_species import data
from cyclopts.structured_species import tools as strtools
from cyclopts.problems import Solver

def test_pnt():
    p = spmod.Point({'foo': 'bar', 'n_rxtr': 100})
    assert_equal(p.n_rxtr, 100) # not default
    assert_equal(p.f_rxtr, 0) # default
    assert_false(hasattr(p.n_rxtr, 'foo'))

    q = spmod.Point({'foo': 'bar', 'n_rxtr': 100})
    assert_equal(p, q)

def test_basics():
    sp = spmod.StructuredRequest()
    
    exp = 'StructuredRequest'
    obs = sp.name
    assert_equal(obs, exp)
    
    assert_true(isinstance(sp.family, ResourceExchange))

def test_read_space():
    space = {'n_rxtr': [100], 'f_fc': range(3)}
    sp = spmod.StructuredRequest()
    
    sp.read_space(space)
    assert_equal(sp.n_points, 3)
    
    exp = [spmod.Point({'n_rxtr': 100, 'f_fc': i}) \
               for i in range(3)].sort(key=lambda x: x.f_fc)
    obs = [p for p in sp.points()].sort(key=lambda x: x.f_fc)
    assert_equal(obs, exp)

def test_write_point():    
    sp = spmod.StructuredRequest()
    param_tbl, sum_tbl = sp.register_tables(None, 'foo')
    uid = uuid.uuid4()
    p = spmod.Point({'n_rxtr': 100})
    sp.record_point(p, uid, {sp.param_tbl_name: param_tbl, sp.sum_tbl_name: sum_tbl})

    ## params are alphabetcially ordered
    exp_ary = [
        uid.bytes,
        ResourceExchange().name,
        0, # f_fc
        0, # f_loc
        1, # f_mox
        0, # f_rxtr
        10, # n_reg
        100, # n_rxtr, non defaults
        1, # r_inv_proc
        1, # r_l_c
        0.5, # r_s_mox
        1, # r_s_mox_uox
        0.5, # r_s_th
        0.5, # r_s_thox
        1, # r_t_f
        0, # r_th_pu
        -1, # seed
        ]
    obs_ary = param_tbl._data[0]
    for i, k in enumerate(p._parameters()):
        obs = obs_ary[i + 2] # skip uuid, name
        exp = exp_ary[i + 2]
        print(k, spmod.Point.parameters[k], obs, exp)
        if cyctools.seq_not_str(exp):
            assert_array_almost_equal(obs, exp)
        else:
            assert_almost_equal(obs, exp)

def test_th_reactors():
    gids = cyctools.Incrementer()
    nids = cyctools.Incrementer()    

    # once through, thermal
    p = spmod.Point({'f_fc': 0, 'f_mox': 0.25})
    kind = data.Reactors.th
    r = spmod.Reactor(kind, p, gids, nids)    
    assert_equal(r.kind, kind)
    assert_equal(len(r.nodes), 1)
    assert_equal(len(r.commod_to_nodes[data.Commodities.uox]), 1)
    assert_almost_equal(r.group.caps[0], data.fuel_unit * data.request_qtys[kind])
    assert_almost_equal(r.group.qty, data.fuel_unit * data.request_qtys[kind])

    # thox recycle, thermal, n assemblies
    p = spmod.Point({'f_fc': 2, 'f_rxtr': 1, 'f_mox': 0.25})
    kind = data.Reactors.th
    r = spmod.Reactor(kind, p, gids, nids)
    base_qty = 1400 * 12.5 / math.floor(157 / 4.)
    assert_equal(len(r.nodes), int(math.ceil(1.5 * data.n_assemblies[kind])))
    assert_equal(len(r.commod_to_nodes[data.Commodities.uox]), 
                 data.n_assemblies[kind])
    assert_almost_equal(r.commod_to_nodes[data.Commodities.uox][0].qty,
                        base_qty)
    assert_equal(len(r.commod_to_nodes[data.Commodities.th_mox]), 
                 int(math.ceil(0.25 * data.n_assemblies[kind])))
    assert_almost_equal(r.commod_to_nodes[data.Commodities.th_mox][0].qty,
                        base_qty * 0.07)
    assert_equal(len(r.commod_to_nodes[data.Commodities.f_mox]), 
                 int(math.ceil(0.25 * data.n_assemblies[kind])))
    assert_almost_equal(r.commod_to_nodes[data.Commodities.f_mox][0].qty,
                        base_qty * 0.07)    
    assert_almost_equal(r.group.caps[0], data.fuel_unit * data.request_qtys[kind])
    assert_almost_equal(r.group.qty, data.fuel_unit * data.request_qtys[kind])

def test_mox_reactors():
    gids = cyctools.Incrementer()
    nids = cyctools.Incrementer()    

    # mox recycle, mox
    p = spmod.Point({'f_fc': 1})
    kind = data.Reactors.f_mox
    r = spmod.Reactor(kind, p, gids, nids)
    assert_equal(len(r.nodes), 3)
    assert_equal(len(r.commod_to_nodes[data.Commodities.uox]), 1)
    assert_equal(len(r.commod_to_nodes[data.Commodities.th_mox]), 1)
    assert_equal(len(r.commod_to_nodes[data.Commodities.f_mox]), 1)
    assert_almost_equal(r.group.caps[0], data.fuel_unit * data.request_qtys[kind])
    assert_almost_equal(r.group.qty, data.fuel_unit * data.request_qtys[kind])

    # thox recycle, mox, n assemblies
    p = spmod.Point({'f_fc': 2, 'f_rxtr': 1})
    kind = data.Reactors.f_mox
    r = spmod.Reactor(kind, p, gids, nids)
    base_qty = 1400 / math.floor(369 / 4.)
    assert_equal(len(r.nodes), 4 * data.n_assemblies[kind])
    assert_equal(len(r.commod_to_nodes[data.Commodities.uox]), 
                 data.n_assemblies[kind])
    assert_almost_equal(r.commod_to_nodes[data.Commodities.uox][0].qty,
                        base_qty)
    assert_equal(len(r.commod_to_nodes[data.Commodities.th_mox]), 
                 data.n_assemblies[kind])
    assert_almost_equal(r.commod_to_nodes[data.Commodities.th_mox][0].qty,
                        base_qty * 0.2)
    assert_equal(len(r.commod_to_nodes[data.Commodities.f_mox]), 
                 data.n_assemblies[kind])
    assert_almost_equal(r.commod_to_nodes[data.Commodities.f_mox][0].qty,
                        base_qty * 0.2)
    assert_equal(len(r.commod_to_nodes[data.Commodities.f_thox]), 
                 data.n_assemblies[kind])    
    assert_almost_equal(r.commod_to_nodes[data.Commodities.f_thox][0].qty,
                        base_qty * 0.2)
    assert_almost_equal(r.group.caps[0], data.fuel_unit * data.request_qtys[kind])
    assert_almost_equal(r.group.qty, data.fuel_unit * data.request_qtys[kind])

def test_thox_reactors():
    gids = cyctools.Incrementer()
    nids = cyctools.Incrementer()    

    # thox recycle, thox
    p = spmod.Point({'f_fc': 2, 'f_rxtr': 1})
    kind = data.Reactors.f_thox
    r = spmod.Reactor(kind, p, gids, nids)
    base_qty = 1400 / math.floor(369 / 4.)
    assert_equal(len(r.nodes), 4 * data.n_assemblies[kind])
    assert_equal(len(r.commod_to_nodes[data.Commodities.uox]), 
                 data.n_assemblies[kind])
    assert_almost_equal(r.commod_to_nodes[data.Commodities.uox][0].qty,
                        base_qty)
    assert_equal(len(r.commod_to_nodes[data.Commodities.th_mox]), 
                 data.n_assemblies[kind])
    assert_almost_equal(r.commod_to_nodes[data.Commodities.th_mox][0].qty,
                        base_qty * 0.2)
    assert_equal(len(r.commod_to_nodes[data.Commodities.f_mox]), 
                 data.n_assemblies[kind])
    assert_almost_equal(r.commod_to_nodes[data.Commodities.f_mox][0].qty,
                        base_qty * 0.2)
    assert_equal(len(r.commod_to_nodes[data.Commodities.f_thox]), 
                 data.n_assemblies[kind])    
    assert_almost_equal(r.commod_to_nodes[data.Commodities.f_thox][0].qty,
                        base_qty * 0.2)    
    assert_almost_equal(r.group.caps[0], data.fuel_unit * data.request_qtys[kind])
    assert_almost_equal(r.group.qty, data.fuel_unit * data.request_qtys[kind])

def test_conv():
    exp = 1.33 # from wise-uranium.org/nfcue.html with assays as stated
    obs = strtools.conv_ratio(data.Supports.uox)
    assert_almost_equal(obs, exp, places=2)

def test_supplier():
    gids = cyctools.Incrementer()
    p = spmod.Point({'r_inv_proc': 0.33})
    
    kind = data.Supports.uox
    rate = 3.3e6 / 12
    s = spmod.Supplier(kind, p, gids)
    assert_almost_equal(s.group.caps[0], rate)
    assert_almost_equal(s.group.caps[1], rate * 0.33 * strtools.conv_ratio(kind))

    kind = data.Supports.th_mox
    rate = 800e3 / 12
    s = spmod.Supplier(kind, p, gids)
    assert_almost_equal(s.group.caps[0], rate)
    assert_almost_equal(s.group.caps[1], rate * 0.33 * strtools.conv_ratio(kind))

    kind = data.Supports.f_mox
    rate = 800e3 / 12
    s = spmod.Supplier(kind, p, gids)
    assert_almost_equal(s.group.caps[0], rate)
    assert_almost_equal(s.group.caps[1], rate * 0.33 * strtools.conv_ratio(kind))

    kind = data.Supports.f_thox
    rate = 800e3 / 12
    s = spmod.Supplier(kind, p, gids)
    assert_almost_equal(s.group.caps[0], rate)
    assert_almost_equal(s.group.caps[1], rate * 0.33 * strtools.conv_ratio(kind))
    
def assert_rcoeffs_equal(arc, commod, rkind, skind, n):
    r_coeffs = [1 / data.relative_qtys[rkind][commod]]
    assert_array_almost_equal(arc.ucaps, r_coeffs)

def assert_scoeffs_equal(arc, commod, rkind, skind, n, enr):
    qty = data.fuel_unit * data.request_qtys[rkind] * \
        data.relative_qtys[rkind][commod] / n
    s_coeffs = [data.converters[skind]['proc'](qty, enr, commod) / qty,
                data.converters[skind]['inv'](qty, enr, commod) / qty]
    assert_array_almost_equal(arc.vcaps, s_coeffs)

def test_one_supply():
    gids = cyctools.Incrementer()
    nids = cyctools.Incrementer()
    sp = spmod.StructuredRequest()

    rkind = data.Reactors.f_mox
    skind = data.Supports.f_mox
    commod = data.Commodities.f_mox
    p = spmod.Point({'f_fc': 2, 'f_rxtr': 0})
    r = spmod.Reactor(rkind, p, gids, nids)
    s = spmod.Supplier(skind, p, gids)

    arcs = sp._generate_supply(p, commod, r, s)
    assert_equal(len(arcs), 1)
    assert_equal(len(s.nodes), 1)    

    a = arcs[0]
    n_s = s.nodes[0]
    n_r = r.commod_to_nodes[commod][0]
    assert_equal(a.uid, n_r.id)
    assert_equal(a.vid, n_s.id)

    assert_almost_equal(n_s.qty, r.req_qty(commod))

    assert_rcoeffs_equal(a, commod, rkind, skind, 1)
    assert_scoeffs_equal(a, commod, rkind, skind, 1, r.enr(commod))    

def test_th_supply():
    gids = cyctools.Incrementer()
    nids = cyctools.Incrementer()
    sp = spmod.StructuredRequest()
    rkind = data.Reactors.th
    p = spmod.Point({'f_fc': 2, 'f_rxtr': 1, 'f_mox': 0.25})
    r = spmod.Reactor(rkind, p, gids, nids)

    # uox
    skind = data.Supports.uox
    commod = data.Commodities.uox
    s = spmod.Supplier(skind, p, gids)
    arcs = sp._generate_supply(p, commod, r, s)
    assert_equal(len(arcs), data.n_assemblies[rkind])
    assert_equal(len(s.nodes), data.n_assemblies[rkind])    
    assert_almost_equal(s.nodes[0].qty, r.req_qty(commod))
    assert_rcoeffs_equal(arcs[0], commod, rkind, skind, data.n_assemblies[rkind])
    assert_scoeffs_equal(arcs[0], commod, rkind, skind, data.n_assemblies[rkind], 
                         r.enr(commod))    

    # th mox
    skind = data.Supports.th_mox
    commod = data.Commodities.th_mox
    s = spmod.Supplier(skind, p, gids)
    arcs = sp._generate_supply(p, commod, r, s)
    n = int(math.ceil(0.25 * data.n_assemblies[rkind])) 
    assert_equal(len(arcs), n)
    assert_equal(len(s.nodes), n)    
    assert_almost_equal(s.nodes[0].qty, r.req_qty(commod))
    assert_rcoeffs_equal(arcs[0], commod, rkind, skind, data.n_assemblies[rkind])
    assert_scoeffs_equal(arcs[0], commod, rkind, skind, data.n_assemblies[rkind], 
                         r.enr(commod))    

    # f mox
    skind = data.Supports.f_mox
    commod = data.Commodities.f_mox
    s = spmod.Supplier(skind, p, gids)
    arcs = sp._generate_supply(p, commod, r, s)
    assert_equal(len(arcs), n)
    assert_equal(len(s.nodes), n)    
    assert_almost_equal(s.nodes[0].qty, r.req_qty(commod))
    assert_rcoeffs_equal(arcs[0], commod, rkind, skind, data.n_assemblies[rkind])
    assert_scoeffs_equal(arcs[0], commod, rkind, skind, data.n_assemblies[rkind], 
                         r.enr(commod))    
    
def test_fmox_supply():
    gids = cyctools.Incrementer()
    nids = cyctools.Incrementer()
    sp = spmod.StructuredRequest()
    rkind = data.Reactors.f_mox
    p = spmod.Point({'f_fc': 2, 'f_rxtr': 1})
    r = spmod.Reactor(rkind, p, gids, nids)

    # uox
    skind = data.Supports.uox
    commod = data.Commodities.uox
    s = spmod.Supplier(skind, p, gids)
    arcs = sp._generate_supply(p, commod, r, s)
    assert_equal(len(arcs), data.n_assemblies[rkind])
    assert_equal(len(s.nodes), data.n_assemblies[rkind])    
    assert_almost_equal(s.nodes[0].qty, r.req_qty(commod))
    assert_rcoeffs_equal(arcs[0], commod, rkind, skind, data.n_assemblies[rkind])
    assert_scoeffs_equal(arcs[0], commod, rkind, skind, data.n_assemblies[rkind], 
                         r.enr(commod))    

    # th mox
    skind = data.Supports.th_mox
    commod = data.Commodities.th_mox
    s = spmod.Supplier(skind, p, gids)
    arcs = sp._generate_supply(p, commod, r, s)
    assert_equal(len(arcs), data.n_assemblies[rkind])
    assert_equal(len(s.nodes), data.n_assemblies[rkind])    
    assert_almost_equal(s.nodes[0].qty, r.req_qty(commod))
    assert_rcoeffs_equal(arcs[0], commod, rkind, skind, data.n_assemblies[rkind])
    assert_scoeffs_equal(arcs[0], commod, rkind, skind, data.n_assemblies[rkind], 
                         r.enr(commod))    

    # f mox
    skind = data.Supports.f_mox
    commod = data.Commodities.f_mox
    s = spmod.Supplier(skind, p, gids)
    arcs = sp._generate_supply(p, commod, r, s)
    assert_equal(len(arcs), data.n_assemblies[rkind])
    assert_equal(len(s.nodes), data.n_assemblies[rkind])    
    assert_almost_equal(s.nodes[0].qty, r.req_qty(commod))
    assert_rcoeffs_equal(arcs[0], commod, rkind, skind, data.n_assemblies[rkind])
    assert_scoeffs_equal(arcs[0], commod, rkind, skind, data.n_assemblies[rkind], 
                         r.enr(commod))    

    # thox
    skind = data.Supports.f_thox
    commod = data.Commodities.f_thox
    s = spmod.Supplier(skind, p, gids)
    arcs = sp._generate_supply(p, commod, r, s)
    assert_equal(len(arcs), data.n_assemblies[rkind])
    assert_equal(len(s.nodes), data.n_assemblies[rkind])    
    assert_almost_equal(s.nodes[0].qty, r.req_qty(commod))
    assert_rcoeffs_equal(arcs[0], commod, rkind, skind, data.n_assemblies[rkind])
    assert_scoeffs_equal(arcs[0], commod, rkind, skind, data.n_assemblies[rkind], 
                         r.enr(commod))    
    
def test_fmox_supply():
    gids = cyctools.Incrementer()
    nids = cyctools.Incrementer()
    sp = spmod.StructuredRequest()
    rkind = data.Reactors.f_thox
    p = spmod.Point({'f_fc': 2, 'f_rxtr': 1})
    r = spmod.Reactor(rkind, p, gids, nids)

    # uox
    skind = data.Supports.uox
    commod = data.Commodities.uox
    s = spmod.Supplier(skind, p, gids)
    arcs = sp._generate_supply(p, commod, r, s)
    assert_equal(len(arcs), data.n_assemblies[rkind])
    assert_equal(len(s.nodes), data.n_assemblies[rkind])    
    assert_almost_equal(s.nodes[0].qty, r.req_qty(commod))
    assert_rcoeffs_equal(arcs[0], commod, rkind, skind, data.n_assemblies[rkind])
    assert_scoeffs_equal(arcs[0], commod, rkind, skind, data.n_assemblies[rkind], 
                         r.enr(commod))    

    # th mox
    skind = data.Supports.th_mox
    commod = data.Commodities.th_mox
    s = spmod.Supplier(skind, p, gids)
    arcs = sp._generate_supply(p, commod, r, s)
    assert_equal(len(arcs), data.n_assemblies[rkind])
    assert_equal(len(s.nodes), data.n_assemblies[rkind])    
    assert_almost_equal(s.nodes[0].qty, r.req_qty(commod))
    assert_rcoeffs_equal(arcs[0], commod, rkind, skind, data.n_assemblies[rkind])
    assert_scoeffs_equal(arcs[0], commod, rkind, skind, data.n_assemblies[rkind], 
                         r.enr(commod))    

    # f mox
    skind = data.Supports.f_mox
    commod = data.Commodities.f_mox
    s = spmod.Supplier(skind, p, gids)
    arcs = sp._generate_supply(p, commod, r, s)
    assert_equal(len(arcs), data.n_assemblies[rkind])
    assert_equal(len(s.nodes), data.n_assemblies[rkind])    
    assert_almost_equal(s.nodes[0].qty, r.req_qty(commod))
    assert_rcoeffs_equal(arcs[0], commod, rkind, skind, data.n_assemblies[rkind])
    assert_scoeffs_equal(arcs[0], commod, rkind, skind, data.n_assemblies[rkind], 
                         r.enr(commod))    

    # thox
    skind = data.Supports.f_thox
    commod = data.Commodities.f_thox
    s = spmod.Supplier(skind, p, gids)
    arcs = sp._generate_supply(p, commod, r, s)
    assert_equal(len(arcs), data.n_assemblies[rkind])
    assert_equal(len(s.nodes), data.n_assemblies[rkind])    
    assert_almost_equal(s.nodes[0].qty, r.req_qty(commod))
    assert_rcoeffs_equal(arcs[0], commod, rkind, skind, data.n_assemblies[rkind])
    assert_scoeffs_equal(arcs[0], commod, rkind, skind, data.n_assemblies[rkind], 
                         r.enr(commod))    
    
def test_once_through():
    sp = spmod.StructuredRequest()
    d = {
        'n_rxtr': 5,
        'r_t_f': 2./5., 
        'r_th_pu': 1./3.,
        'r_s_mox': 0.5,
        'r_s_thox': 1.,
       }

    d['f_fc'] = 0
    d['r_s_th'] = 1.
    d['r_s_mox_uox'] = 1.
    p = spmod.Point(d)

    # reactors exp
    obs = strtools.reactor_breakdown(p)
    rexp = (5, 0, 0)
    assert_equal(obs, rexp)
    
    # suppliers exp
    obs = strtools.support_breakdown(p)
    sexp = (5, 0, 0, 0, 0)
    assert_equal(obs, sexp)
    
    groups, nodes, arcs = sp.gen_inst(p)
    assert_equal(len(groups), sum(rexp) + sum(sexp))
    assert_equal(len(nodes), rexp[0] + rexp[0] * sexp[0])
    assert_equal(len(arcs), rexp[0] * sexp[0])

def test_mox_recycle():
    sp = spmod.StructuredRequest()
    d = {
        'n_rxtr': 5,
        'r_t_f': 2./5., 
        'r_th_pu': 1./3.,
        'r_s_mox': 1./3.,
        'r_s_thox': 1.,
       }

    d['f_fc'] = 1
    d['r_s_th'] = 3. / 2.
    d['r_s_mox_uox'] = 1. / 3.
    p = spmod.Point(d)

    # reactors exp
    obs = strtools.reactor_breakdown(p)
    rexp = (2, 3, 0)
    assert_equal(obs, rexp)

    # suppliers exp
    obs = strtools.support_breakdown(p)
    sexp = (2, 1, 1, 0, 0)
    assert_equal(obs, sexp)
    
    groups, nodes, arcs = sp.gen_inst(p)
    assert_equal(len(groups), sum(rexp) + sum(sexp))
    rnodes_exp = rexp[0] * 3 + rexp[1] * 3 # rxtrs * n commods
    snodes_exp = sum((sexp[i] * r for i in (0, 1, 2) for r in rexp)) # uox/mox
    assert_equal(len(nodes), rnodes_exp + snodes_exp)
    assert_equal(len(arcs), snodes_exp)

def test_thox_recycle():
    sp = spmod.StructuredRequest()
    d = {
        'n_rxtr': 5,
        'r_t_f': 2./5., 
        'r_th_pu': 1./3.,
        'r_s_mox': 0.5,
        'r_s_thox': 1.,
       }

    d['f_fc'] = 2
    d['r_s_th'] = 3. / 2.
    d['r_s_mox_uox'] = 1. / 3.
    p = spmod.Point(d)

    # reactors exp
    obs = strtools.reactor_breakdown(p)
    rexp = (2, 2, 1)
    assert_equal(obs, rexp)
    
    # suppliers exp
    obs = strtools.support_breakdown(p)
    sexp = (2, 1, 1, 1, 0)
    assert_equal(obs, sexp)
    
    groups, nodes, arcs = sp.gen_inst(p)
    assert_equal(len(groups), sum(rexp) + sum(sexp))
    groups, nodes, arcs = sp.gen_inst(p)
    assert_equal(len(groups), sum(rexp) + sum(sexp))
    rnodes_exp = rexp[0] * 3 + rexp[1] * 4 + rexp[2] * 4 # rxtrs * n commods
    snodes_exp = sum((sexp[i] * r for i in (0, 1, 2) for r in rexp)) + \
        sum((sexp[3] * rexp[i] for i in (1, 2))) # uox/mox then thox
    assert_equal(len(nodes), rnodes_exp + snodes_exp)
    assert_equal(len(arcs), snodes_exp)
    
def test_mininmal_run():
    fname = 'structured_request_conv.py'
    base = os.path.dirname(os.path.abspath(__file__))
    fpath = os.path.join(base, 'files', fname)

    sp = spmod.StructuredRequest()
    fam = ResourceExchange()
    rc = cyctools.parse_rc(fpath)

    sp.read_space(rc._dict)
    assert_equal(sp.n_points, 1)
    for point in sp.points(): # there should only be one
        groups, nodes, arcs = sp.gen_inst(point)

    assert_equal(len(groups), 7)
    assert_equal(len(nodes), 22)
    assert_equal(len(arcs), 11)

    obs_prefs = [a.pref for a in arcs]
    exp_prefs = [0.5, 1.0, 0.1, 0.1, 0.5, 1.0, 0.25, 0.1, 0.25, 0.5, 1.0]
    assert_equal(obs_prefs, exp_prefs)

    solver = Solver('cbc')
    soln = fam.run_inst((groups, nodes, arcs), solver)
    
    print('flows:', soln.flows)
    assert_almost_equal(soln.flows[0], 17500) # uox for thermal reactors
    assert_almost_equal(soln.flows[5], 280) # fmox for fmox reactors
    assert_almost_equal(soln.flows[10], 280) # fthox for fthox reactors
