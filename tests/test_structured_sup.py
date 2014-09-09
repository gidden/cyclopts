from cyclopts.structured_species import supply as spmod

import uuid
import math
import os

from nose.tools import assert_equal, assert_almost_equal, assert_true, assert_false
from numpy.testing import assert_array_almost_equal

from cyclopts import tools
from cyclopts.exchange_family import ResourceExchange
from cyclopts.structured_species import data as data
from cyclopts.problems import Solver

def test_basics():
    sp = spmod.StructuredSupply()    
    exp = 'StructuredSupply'
    obs = sp.name
    assert_equal(obs, exp)
    assert_true(isinstance(sp.family, ResourceExchange))

def test_pnt():
    p = spmod.Point({'foo': 'bar', 'n_rxtr': 100, 'd_th': [0.7, 0.2, 0.1]})
    assert_equal(p.n_rxtr, 100) # not default
    assert_equal(p.d_th, [0.7, 0.2, 0.1]) # not default
    assert_equal(p.f_rxtr, 0) # default
    assert_false(hasattr(p.n_rxtr, 'foo'))

    q = spmod.Point({'foo': 'bar', 'n_rxtr': 100, 'd_th': [0.7, 0.2, 0.1]})
    assert_equal(p, q)

def test_read_space():
    space = {'n_rxtr': range(3), 'd_th': [0.7, 0.2, 0.1]}
    sp = spmod.StructuredSupply()
    
    sp.read_space(space)
    assert_equal(sp.n_points, 3)
    
    exp = [spmod.Point({'n_rxtr': i, 'd_th': [0.7, 0.2, 0.1]}) \
               for i in range(3)].sort(key=lambda x: x.n_rxtr)
    obs = [p for p in sp.points()].sort(key=lambda x: x.n_rxtr)
    assert_equal(obs, exp)

def test_write_point():    
    sp = spmod.StructuredSupply()
    param_tbl, sum_tbl = sp.register_tables(None, 'foo')
    uid = uuid.uuid4()
    p = spmod.Point({'d_th': [0.7, 0.2, 0.1]})
    sp.record_point(p, uid, {sp.param_tbl_name: param_tbl, sp.sum_tbl_name: sum_tbl})

    ## params are alphabetcially ordered 
    exp = (
        uid.bytes,
        ResourceExchange().name,
        [0.7, 0.2, 0.1], # d_th, non defaults
        [0, 0, 1, 0], # d_f_mox
        [0, 0, 0, 1], # d_f_thox
        0, # f_fc
        0, # f_loc
        1, # f_mox
        0.1, # f_repo
        0, # f_rxtr
        10, # n_reg
        1, # n_rxtr
        1, # r_inv_proc
        1, # r_l_c
        0.5, # r_s_mox
        1, # r_s_mox_uox
        0.5, # r_s_th
        0.5, # r_s_thox
        1, # r_t_f
        0, # r_th_pu
        -1, # seed
        )
    obs = param_tbl._data[0]
    for i, k in enumerate(spmod.parameters):
        print(k)
        assert_equal(obs[i], exp[i])
