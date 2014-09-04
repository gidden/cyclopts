from cyclopts import structured_species as strsp

import uuid
import math

from nose.tools import assert_equal, assert_almost_equal, assert_true, assert_false
from numpy.testing import assert_array_almost_equal

from cyclopts import tools
from cyclopts.exchange_family import ResourceExchange
from cyclopts import structured_species_data as data

def test_pnt():
    p = strsp.Point({'foo': 'bar', 'n_rxtr': 100})
    assert_equal(p.n_rxtr, 100) # not default
    assert_equal(p.f_rxtr, 0) # default
    assert_false(hasattr(p.n_rxtr, 'foo'))

    q = strsp.Point({'foo': 'bar', 'n_rxtr': 100})
    assert_equal(p, q)

def test_request_basics():
    sp = strsp.StructuredRequest()
    
    exp = 'StructuredRequest'
    obs = sp.name
    assert_equal(obs, exp)
    
    assert_true(isinstance(sp.family, ResourceExchange))

def test_request_read_space():
    space = {'n_rxtr': [100], 'f_fc': [0, 1, 2]}
    sp = strsp.StructuredRequest()
    
    sp.read_space(space)
    assert_equal(sp.n_points, 3)
    
    exp = [strsp.Point({'n_rxtr': 100, 'f_fc': i}) \
               for i in range(3)].sort(key=lambda x: x.f_fc)
    obs = [p for p in sp.points()].sort(key=lambda x: x.f_fc)
    assert_equal(obs, exp)

def test_request_write_point():    
    sp = strsp.StructuredRequest()
    tbl = sp.register_tables(None, 'foo')[0]
    uid = uuid.uuid4()
    p = strsp.Point({'n_rxtr': 100})
    sp.record_point(p, uid, {sp.tbl_name: tbl})

    ## params are alphabetcially ordered 
    # f_fc
    # f_loc
    # f_mox
    # f_rxtr
    # n_reg
    # n_rxtr
    # r_inv_proc
    # r_l_c
    # r_s_mox
    # r_s_mox_uox
    # r_s_th
    # r_s_thox
    # r_t_f
    # r_th_pu    
    # seed
    exp = (
        uid.bytes,
        ResourceExchange().name,
        0,
        0,
        1,
        0,
        10,
        100, # non defaults
        1,
        1,
        0.5,
        1,
        0.5,
        0.5,
        1,
        0,
        -1,
        )
    obs = tbl._data[0]
    for i, k in enumerate(strsp.parameters):
        print(k)
        if isinstance(exp[i], float):
            assert_almost_equal(obs[i], exp[i])
        else:
            assert_equal(obs[i], exp[i])
    
def test_reactor_breakdown():
    sp = strsp.StructuredRequest()
    d = {
        'n_rxtr': 101,
        'r_t_f': 0.23,
        'r_th_pu': 0.15,
        }

    d['f_fc'] = 0
    p = strsp.Point(d)    
    obs = sp._reactor_breakdown(p)
    exp = (101, 0, 0)
    assert_equal(obs, exp)

    d['f_fc'] = 1
    p = strsp.Point(d)    
    obs = sp._reactor_breakdown(p)
    exp = (23, 66 + 12, 0)
    assert_equal(obs, exp)

    d['f_fc'] = 2
    p = strsp.Point(d)    
    obs = sp._reactor_breakdown(p)
    exp = (23, 66, 12)
    assert_equal(obs, exp)

def test_supplier_breakdown():
    sp = strsp.StructuredRequest()
    d = {
        'n_rxtr': 101,
        'r_t_f': 0.23,
        'r_th_pu': 0.15,
        'r_s_th': 0.13,
        'r_s_mox_uox': 0.75,
        'r_s_mox': 0.45,
        'r_s_thox': 0.39,
        }

    d['f_fc'] = 0
    p = strsp.Point(d)
    obs = sp._supplier_breakdown(p) 
    exp = (13, 0, 0, 0)    
    assert_equal(obs, exp)

    d['f_fc'] = 1
    p = strsp.Point(d)
    obs = sp._supplier_breakdown(p) 
    exp = (2, 1, 35, 0)    
    assert_equal(obs, exp)
    
    d['f_fc'] = 2
    p = strsp.Point(d)
    obs = sp._supplier_breakdown(p) 
    exp = (2, 1, 30, 5)    
    assert_equal(obs, exp)

def test_th_reactors():
    gids = tools.Incrementer()
    nids = tools.Incrementer()    

    # once through, thermal
    p = strsp.Point({'f_fc': 0, 'f_mox': 0.25})
    kind = data.Reactors.th
    r = strsp.Reactor(kind, p, gids, nids)    
    assert_equal(r.kind, kind)
    assert_equal(len(r.nodes), 1)
    assert_equal(len(r.commod_to_nodes[data.Commodities.uox]), 1)
    assert_almost_equal(r.group.caps[0], data.fuel_unit * data.request_qtys[kind])
    assert_almost_equal(r.group.qty, data.fuel_unit * data.request_qtys[kind])

    # thox recycle, thermal, n assemblies
    p = strsp.Point({'f_fc': 2, 'f_rxtr': 1, 'f_mox': 0.25})
    kind = data.Reactors.th
    r = strsp.Reactor(kind, p, gids, nids)
    base_qty = 1400 * 12.5 / math.floor(157 / 4.)
    assert_equal(len(r.nodes), int(math.ceil(1.5 * data.n_assemblies[kind])))
    assert_equal(len(r.commod_to_nodes[data.Commodities.uox]), 
                 data.n_assemblies[kind])
    assert_almost_equal(r.commod_to_nodes[data.Commodities.uox][0].qty,
                        base_qty)
    assert_equal(len(r.commod_to_nodes[data.Commodities.th_mox]), 
                 int(math.ceil(0.25 * data.n_assemblies[kind])))
    assert_almost_equal(r.commod_to_nodes[data.Commodities.th_mox][0].qty,
                        base_qty * 0.1)
    assert_equal(len(r.commod_to_nodes[data.Commodities.f_mox]), 
                 int(math.ceil(0.25 * data.n_assemblies[kind])))
    assert_almost_equal(r.commod_to_nodes[data.Commodities.f_mox][0].qty,
                        base_qty * 0.1)    
    assert_almost_equal(r.group.caps[0], data.fuel_unit * data.request_qtys[kind])
    assert_almost_equal(r.group.qty, data.fuel_unit * data.request_qtys[kind])

def test_mox_reactors():
    gids = tools.Incrementer()
    nids = tools.Incrementer()    

    # mox recycle, mox
    p = strsp.Point({'f_fc': 1})
    kind = data.Reactors.f_mox
    r = strsp.Reactor(kind, p, gids, nids)
    assert_equal(len(r.nodes), 3)
    assert_equal(len(r.commod_to_nodes[data.Commodities.uox]), 1)
    assert_equal(len(r.commod_to_nodes[data.Commodities.th_mox]), 1)
    assert_equal(len(r.commod_to_nodes[data.Commodities.f_mox]), 1)
    assert_almost_equal(r.group.caps[0], data.fuel_unit * data.request_qtys[kind])
    assert_almost_equal(r.group.qty, data.fuel_unit * data.request_qtys[kind])

    # thox recycle, mox, n assemblies
    p = strsp.Point({'f_fc': 2, 'f_rxtr': 1})
    kind = data.Reactors.f_mox
    r = strsp.Reactor(kind, p, gids, nids)
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
    gids = tools.Incrementer()
    nids = tools.Incrementer()    

    # thox recycle, thox
    p = strsp.Point({'f_fc': 2, 'f_rxtr': 1})
    kind = data.Reactors.f_thox
    r = strsp.Reactor(kind, p, gids, nids)
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
    obs = data.conv_ratio(data.Suppliers.uox)
    assert_almost_equal(obs, exp, places=2)

def test_supplier():
    gids = tools.Incrementer()
    p = strsp.Point({'r_inv_proc': 0.33})
    
    kind = data.Suppliers.uox
    rate = 3.3e6 / 12
    s = strsp.Supplier(kind, p, gids)
    assert_almost_equal(s.group.caps[0], rate)
    assert_almost_equal(s.group.caps[1], rate * 0.33 * data.conv_ratio(kind))

    kind = data.Suppliers.th_mox
    rate = 800e3 / 12
    s = strsp.Supplier(kind, p, gids)
    assert_almost_equal(s.group.caps[0], rate)
    assert_almost_equal(s.group.caps[1], rate * 0.33 * data.conv_ratio(kind))

    kind = data.Suppliers.f_mox
    rate = 800e3 / 12
    s = strsp.Supplier(kind, p, gids)
    assert_almost_equal(s.group.caps[0], rate)
    assert_almost_equal(s.group.caps[1], rate * 0.33 * data.conv_ratio(kind))

    kind = data.Suppliers.f_thox
    rate = 800e3 / 12
    s = strsp.Supplier(kind, p, gids)
    assert_almost_equal(s.group.caps[0], rate)
    assert_almost_equal(s.group.caps[1], rate * 0.33 * data.conv_ratio(kind))
    
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
    gids = tools.Incrementer()
    nids = tools.Incrementer()
    sp = strsp.StructuredRequest()

    rkind = data.Reactors.f_mox
    skind = data.Suppliers.f_mox
    commod = data.Commodities.f_mox
    p = strsp.Point({'f_fc': 2, 'f_rxtr': 0})
    r = strsp.Reactor(rkind, p, gids, nids)
    s = strsp.Supplier(skind, p, gids)

    arcs = sp._generate_supply(p, commod, r, s)
    assert_equal(len(arcs), 1)
    assert_equal(len(s.nodes), 1)    

    a = arcs[0]
    n_s = s.nodes[0]
    n_r = r.commod_to_nodes[commod][0]
    assert_equal(a.uid, n_r.id)
    assert_equal(a.vid, n_s.id)
    
    assert_rcoeffs_equal(a, commod, rkind, skind, 1)
    assert_scoeffs_equal(a, commod, rkind, skind, 1, r.enr(commod))    

def test_th_supply():
    gids = tools.Incrementer()
    nids = tools.Incrementer()
    sp = strsp.StructuredRequest()
    rkind = data.Reactors.th
    p = strsp.Point({'f_fc': 2, 'f_rxtr': 1, 'f_mox': 0.25})
    r = strsp.Reactor(rkind, p, gids, nids)

    # uox
    skind = data.Suppliers.uox
    commod = data.Commodities.uox
    s = strsp.Supplier(skind, p, gids)
    arcs = sp._generate_supply(p, commod, r, s)
    assert_equal(len(arcs), data.n_assemblies[rkind])
    assert_equal(len(s.nodes), data.n_assemblies[rkind])    
    assert_rcoeffs_equal(arcs[0], commod, rkind, skind, data.n_assemblies[rkind])
    assert_scoeffs_equal(arcs[0], commod, rkind, skind, data.n_assemblies[rkind], 
                         r.enr(commod))    

    # th mox
    skind = data.Suppliers.th_mox
    commod = data.Commodities.th_mox
    s = strsp.Supplier(skind, p, gids)
    arcs = sp._generate_supply(p, commod, r, s)
    n = int(math.ceil(0.25 * data.n_assemblies[rkind])) 
    assert_equal(len(arcs), n)
    assert_equal(len(s.nodes), n)    
    assert_rcoeffs_equal(arcs[0], commod, rkind, skind, data.n_assemblies[rkind])
    assert_scoeffs_equal(arcs[0], commod, rkind, skind, data.n_assemblies[rkind], 
                         r.enr(commod))    

    # f mox
    skind = data.Suppliers.f_mox
    commod = data.Commodities.f_mox
    s = strsp.Supplier(skind, p, gids)
    arcs = sp._generate_supply(p, commod, r, s)
    assert_equal(len(arcs), n)
    assert_equal(len(s.nodes), n)    
    assert_rcoeffs_equal(arcs[0], commod, rkind, skind, data.n_assemblies[rkind])
    assert_scoeffs_equal(arcs[0], commod, rkind, skind, data.n_assemblies[rkind], 
                         r.enr(commod))    
    
def test_fmox_supply():
    gids = tools.Incrementer()
    nids = tools.Incrementer()
    sp = strsp.StructuredRequest()
    rkind = data.Reactors.f_mox
    p = strsp.Point({'f_fc': 2, 'f_rxtr': 1})
    r = strsp.Reactor(rkind, p, gids, nids)

    # uox
    skind = data.Suppliers.uox
    commod = data.Commodities.uox
    s = strsp.Supplier(skind, p, gids)
    arcs = sp._generate_supply(p, commod, r, s)
    assert_equal(len(arcs), data.n_assemblies[rkind])
    assert_equal(len(s.nodes), data.n_assemblies[rkind])    
    assert_rcoeffs_equal(arcs[0], commod, rkind, skind, data.n_assemblies[rkind])
    assert_scoeffs_equal(arcs[0], commod, rkind, skind, data.n_assemblies[rkind], 
                         r.enr(commod))    

    # th mox
    skind = data.Suppliers.th_mox
    commod = data.Commodities.th_mox
    s = strsp.Supplier(skind, p, gids)
    arcs = sp._generate_supply(p, commod, r, s)
    assert_equal(len(arcs), data.n_assemblies[rkind])
    assert_equal(len(s.nodes), data.n_assemblies[rkind])    
    assert_rcoeffs_equal(arcs[0], commod, rkind, skind, data.n_assemblies[rkind])
    assert_scoeffs_equal(arcs[0], commod, rkind, skind, data.n_assemblies[rkind], 
                         r.enr(commod))    

    # f mox
    skind = data.Suppliers.f_mox
    commod = data.Commodities.f_mox
    s = strsp.Supplier(skind, p, gids)
    arcs = sp._generate_supply(p, commod, r, s)
    assert_equal(len(arcs), data.n_assemblies[rkind])
    assert_equal(len(s.nodes), data.n_assemblies[rkind])    
    assert_rcoeffs_equal(arcs[0], commod, rkind, skind, data.n_assemblies[rkind])
    assert_scoeffs_equal(arcs[0], commod, rkind, skind, data.n_assemblies[rkind], 
                         r.enr(commod))    

    # thox
    skind = data.Suppliers.f_thox
    commod = data.Commodities.f_thox
    s = strsp.Supplier(skind, p, gids)
    arcs = sp._generate_supply(p, commod, r, s)
    assert_equal(len(arcs), data.n_assemblies[rkind])
    assert_equal(len(s.nodes), data.n_assemblies[rkind])    
    assert_rcoeffs_equal(arcs[0], commod, rkind, skind, data.n_assemblies[rkind])
    assert_scoeffs_equal(arcs[0], commod, rkind, skind, data.n_assemblies[rkind], 
                         r.enr(commod))    
    
def test_fmox_supply():
    gids = tools.Incrementer()
    nids = tools.Incrementer()
    sp = strsp.StructuredRequest()
    rkind = data.Reactors.f_thox
    p = strsp.Point({'f_fc': 2, 'f_rxtr': 1})
    r = strsp.Reactor(rkind, p, gids, nids)

    # uox
    skind = data.Suppliers.uox
    commod = data.Commodities.uox
    s = strsp.Supplier(skind, p, gids)
    arcs = sp._generate_supply(p, commod, r, s)
    assert_equal(len(arcs), data.n_assemblies[rkind])
    assert_equal(len(s.nodes), data.n_assemblies[rkind])    
    assert_rcoeffs_equal(arcs[0], commod, rkind, skind, data.n_assemblies[rkind])
    assert_scoeffs_equal(arcs[0], commod, rkind, skind, data.n_assemblies[rkind], 
                         r.enr(commod))    

    # th mox
    skind = data.Suppliers.th_mox
    commod = data.Commodities.th_mox
    s = strsp.Supplier(skind, p, gids)
    arcs = sp._generate_supply(p, commod, r, s)
    assert_equal(len(arcs), data.n_assemblies[rkind])
    assert_equal(len(s.nodes), data.n_assemblies[rkind])    
    assert_rcoeffs_equal(arcs[0], commod, rkind, skind, data.n_assemblies[rkind])
    assert_scoeffs_equal(arcs[0], commod, rkind, skind, data.n_assemblies[rkind], 
                         r.enr(commod))    

    # f mox
    skind = data.Suppliers.f_mox
    commod = data.Commodities.f_mox
    s = strsp.Supplier(skind, p, gids)
    arcs = sp._generate_supply(p, commod, r, s)
    assert_equal(len(arcs), data.n_assemblies[rkind])
    assert_equal(len(s.nodes), data.n_assemblies[rkind])    
    assert_rcoeffs_equal(arcs[0], commod, rkind, skind, data.n_assemblies[rkind])
    assert_scoeffs_equal(arcs[0], commod, rkind, skind, data.n_assemblies[rkind], 
                         r.enr(commod))    

    # thox
    skind = data.Suppliers.f_thox
    commod = data.Commodities.f_thox
    s = strsp.Supplier(skind, p, gids)
    arcs = sp._generate_supply(p, commod, r, s)
    assert_equal(len(arcs), data.n_assemblies[rkind])
    assert_equal(len(s.nodes), data.n_assemblies[rkind])    
    assert_rcoeffs_equal(arcs[0], commod, rkind, skind, data.n_assemblies[rkind])
    assert_scoeffs_equal(arcs[0], commod, rkind, skind, data.n_assemblies[rkind], 
                         r.enr(commod))    
    
def test_once_through():
    sp = strsp.StructuredRequest()
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
    p = strsp.Point(d)

    # reactors exp
    obs = sp._reactor_breakdown(p)
    rexp = (5, 0, 0)
    assert_equal(obs, rexp)
    
    # suppliers exp
    obs = sp._supplier_breakdown(p)
    sexp = (5, 0, 0, 0)
    assert_equal(obs, sexp)
    
    groups, nodes, arcs = sp.gen_inst(p)
    assert_equal(len(groups), sum(rexp) + sum(sexp))
    assert_equal(len(nodes), rexp[0] + rexp[0] * sexp[0])
    assert_equal(len(arcs), rexp[0] * sexp[0])

def test_mox_recycle():
    sp = strsp.StructuredRequest()
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
    p = strsp.Point(d)

    # reactors exp
    obs = sp._reactor_breakdown(p)
    rexp = (2, 3, 0)
    assert_equal(obs, rexp)

    # suppliers exp
    obs = sp._supplier_breakdown(p)
    sexp = (2, 1, 1, 0)
    assert_equal(obs, sexp)
    
    groups, nodes, arcs = sp.gen_inst(p)
    assert_equal(len(groups), sum(rexp) + sum(sexp))
    rnodes_exp = rexp[0] * 3 + rexp[1] * 3 # rxtrs * n commods
    snodes_exp = sum((sexp[i] * r for i in (0, 1, 2) for r in rexp)) # uox/mox
    assert_equal(len(nodes), rnodes_exp + snodes_exp)
    assert_equal(len(arcs), snodes_exp)

def test_thox_recycle():
    sp = strsp.StructuredRequest()
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
    p = strsp.Point(d)

    # reactors exp
    obs = sp._reactor_breakdown(p)
    rexp = (2, 2, 1)
    assert_equal(obs, rexp)
    
    # suppliers exp
    obs = sp._supplier_breakdown(p)
    sexp = (2, 1, 1, 1)
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

def test_region():
    assert_equal(strsp.region(0.42, n_reg=5), 2)
    assert_equal(strsp.region(0.42, n_reg=10), 4)
    assert_equal(strsp.region(0.72, n_reg=5), 3)
    assert_equal(strsp.region(0.72, n_reg=10), 7)

def test_pref():
    base, rloc, sloc, n_reg, ratio = 0.5, 0.42, 0.72, 5, 0.33
    
    fidelity = 0
    obs = strsp.preference(base, rloc, sloc, fidelity, ratio, n_reg)
    exp = base
    assert_equal(obs, exp)

    fidelity = 1
    obs = strsp.preference(base, rloc, sloc, fidelity, ratio, n_reg)
    exp = base + ratio * math.exp(-1)
    assert_almost_equal(obs, exp)

    fidelity = 2
    obs = strsp.preference(base, rloc, sloc, fidelity, ratio, n_reg)
    exp = base + ratio * (math.exp(-1) + math.exp(rloc - sloc)) / 2
    assert_almost_equal(obs, exp)
    
