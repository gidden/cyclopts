from cyclopts.structured_species import supply as spmod

from nose.tools import assert_equal, assert_almost_equal, assert_true, assert_false
from numpy.testing import assert_array_almost_equal

import uuid
import math
import os
from collections import Sequence

from cyclopts import tools as cyctools
from cyclopts.exchange_family import ResourceExchange
from cyclopts.structured_species import data as data
from cyclopts.structured_species import tools as strtools
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
    print('space', sp.space)
    assert_equal(sp.n_points, 3)
    
    exp = [spmod.Point({'n_rxtr': i, 'd_th': [0.7, 0.2, 0.1]}) \
               for i in range(3)].sort(key=lambda x: x.n_rxtr)
    obs = [p for p in sp.points()].sort(key=lambda x: x.n_rxtr)
    assert_equal(obs, exp)

    space = {'n_rxtr': range(5, 8), 'd_th': [range(3), range(3)]}
    sp.read_space(space)
    print('space', sp.space)
    assert_equal(sp.n_points, 6)

def test_write_point():    
    sp = spmod.StructuredSupply()
    param_tbl, sum_tbl = sp.register_tables(None, 'foo')
    uid = uuid.uuid4()
    p = spmod.Point({'d_th': [0.7, 0.2, 0.1]})
    sp.record_point(p, uid, {sp.param_tbl_name: param_tbl, sp.sum_tbl_name: sum_tbl})

    ## params are alphabetcially ordered 
    exp_ary = [
        uid.bytes,
        ResourceExchange().name,
        [0., 0., 1., 0.], # d_f_mox
        [0., 0., 0., 1.], # d_f_thox
        [0.7, 0.2, 0.1], # d_th, non defaults
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
    
def test_requester():
    p = spmod.Point({'d_th': [0.7, 0.2, 0.1]})
    gids = cyctools.Incrementer()
    nids = cyctools.Incrementer()    

    # recycle requester
    kind = data.Supports.f_mox
    r = spmod.Requester(kind, p, gids, nids)
    assert_equal(r.kind, kind)
    assert_equal(len(r.nodes), len(data.sup_pref_basis[kind].keys()))
    for commod in data.sup_pref_basis[kind].keys():
        assert_equal(len(r.commod_to_nodes[commod]), 1)
    assert_equal(len(r.group.caps), 1)
    commod, rxtr = data.sup_to_commod[kind], data.sup_to_rxtr[kind]
    mean_enr = strtools.mean_enr(rxtr, commod)
    assert_almost_equal(
        r.group.caps[0], 
        data.sup_rhs[kind] * mean_enr * data.relative_qtys[rxtr][commod])
    assert_equal(r.group.cap_dirs[0], True)
    assert_almost_equal(r.group.qty, data.sup_rhs[kind])

    # repo requester
    kind = data.Supports.repo
    r = spmod.Requester(kind, p, gids, nids)
    assert_equal(r.kind, kind)
    assert_equal(len(r.nodes), len(data.sup_pref_basis[kind].keys()))
    for commod in data.sup_pref_basis[kind].keys():
        assert_equal(len(r.commod_to_nodes[commod]), 1)
    assert_equal(len(r.group.caps), 0)
    assert_almost_equal(r.group.qty, data.sup_rhs[kind])
