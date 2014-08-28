from cyclopts import structured_species as strsp

import uuid

from nose.tools import assert_equal, assert_almost_equal, assert_true, assert_false

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
    # r_s_th
    # r_s_thox
    # r_s_uox_mox
    # r_t_f
    # r_th_pu    
    # seed
    exp = (
        uid.bytes,
        ResourceExchange().name,
        0,
        0,
        1.0/3,
        0,
        10,
        100, # non defaults
        1,
        1,
        0.5,
        0.5,
        0.5,
        1,
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
    p = strsp.Point({
            'n_rxtr': 101,
            'f_fc': 2,
            'r_t_f': 0.23,
            'r_th_pu': 0.15,
            })    
    obs = sp._reactor_breakdown(p)
    exp = (23, 66, 12)
    assert_equal(obs, exp)

def test_supplier_breakdown():
    sp = strsp.StructuredRequest()
    p = strsp.Point({
            'n_rxtr': 101,
            'f_fc': 2,
            'r_t_f': 0.23,
            'r_th_pu': 0.15,
            'r_s_th': 0.13,
            'r_s_uox_mox': 0.75,
            'r_s_mox': 0.45,
            'r_s_thox': 0.39,
            })
    uox, mox, thox = 23, 66, 12
    
    obs = sp._supplier_breakdown(p) 
    exp = (2, 1, 30, 5)    
    assert_equal(obs, exp)


def test_reactor():
    p = strsp.Point()
        
    r = strsp.Reactor(data.Reactors.th, p)

def test_supplier():
    p = strsp.Point()
        
    r = strsp.Supplier(data.Suppliers.uox, p)
    
