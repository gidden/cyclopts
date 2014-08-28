from cyclopts import structured_species as strsp

import uuid

from nose.tools import assert_equal, assert_almost_equal, assert_true, assert_false

from cyclopts.exchange_family import ResourceExchange

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
    # r_s_r
    # r_t_f
    # r_th_pu    
    exp = (
        uid.bytes,
        ResourceExchange().name,
        0,
        0,
        1.0/3,
        0,
        1,
        100, # non defaults
        1,
        1,
        0.5,
        1,
        0,
        )
    obs = tbl._data[0]
    keys = strsp.parameters.keys()
    for i in range(len(exp)):
        if isinstance(exp[i], float):
            assert_almost_equal(obs[i], exp[i])
        else:
            assert_equal(obs[i], exp[i])
    
