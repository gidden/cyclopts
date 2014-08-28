from cyclopts import structured_species as strsp

import uuid

from nose.tools import assert_equal, assert_true, assert_false

from cyclopts.exchange_family import ResourceExchange

def test_pnt():
    p = strsp.Point({'foo': 'bar', 'n_rxtr': 100})
    assert_equal(p.n_rxtr, 100) # not default
    assert_equal(p.f_rxtr, 0) # default
    assert_false(hasattr(p.n_rxtr, 'foo'))

    q = strsp.Point({'foo': 'bar', 'n_rxtr': 100})
    assert_equal(p, q)

def request_basics():
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

def request_write_point():    
    sp = strsp.StructuredRequest()
    tbl = sp.register_tables(None, 'foo')[0]
    uuid = uuid.uuid4()
    p = strsp.Point({'n_rxtr': 100})
    sp.record_point(uuid, p, {sp.tbl_name: tbl})
    
    exp = (
        uuid.bytes,
        ResourceExchange().name,
        0,
        0,
        0,
        100, # non default
        1.0,
        0,
        0.5,
        1./3,
        1.0,
        0,
        1.0,
        )
    obs = tbl._data[0]
    assert_equal(obs, exp)
    
