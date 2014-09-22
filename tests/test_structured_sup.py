from cyclopts.structured_species import supply as spmod

from nose.tools import assert_equal, assert_not_equal, assert_almost_equal, \
    assert_true, assert_false, assert_greater, assert_less
from numpy.testing import assert_array_almost_equal

import uuid
import math
import os
from collections import Sequence, namedtuple
import random

from cyclopts import tools as cyctools
from cyclopts.exchange_family import ResourceExchange
from cyclopts.structured_species import data as data
from cyclopts.structured_species import tools as strtools
from cyclopts.problems import Solver
import cyclopts.exchange_instance as exinst

from utils import assert_cyc_equal

def test_basics():
    sp = spmod.StructuredSupply()    
    exp = 'StructuredSupply'
    obs = sp.name
    assert_equal(obs, exp)
    assert_true(isinstance(sp.family, ResourceExchange))

    base = '/Species/StructuredSupply'
    col, tbl = 'n_repo', 'Summary'
    assert_equal(spmod.PathMap(col).path, base + '/' + tbl)
    col, tbl = 'r_repo', 'Points'
    assert_equal(spmod.PathMap(col).path, base + '/' + tbl)

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
        0, # f_rxtr
        10, # n_reg
        1, # n_rxtr
        1, # r_inv_proc
        1, # r_l_c
        0.1, # r_repo
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
    p = spmod.Point()
    gids = cyctools.Incrementer()
    nids = cyctools.Incrementer()    

    # recycle requester
    kind = data.Supports.f_mox
    r = spmod.Requester(kind, gids, nids)
    assert_equal(r.kind, kind)
    assert_equal(len(r.nodes), len(data.sup_pref_basis[kind].keys()))
    assert_equal(len(r.commod_to_nodes.values()), 
                 len(data.sup_pref_basis[kind].keys()))
    assert_equal(len(r.group.caps), 2)
    commod, rxtr = data.sup_to_commod[kind], data.sup_to_rxtr[kind]
    mean_enr = strtools.mean_enr(rxtr, commod)
    assert_array_almost_equal(
        r.group.caps, 
        [data.sup_rhs[kind], 
         data.sup_rhs[kind] * mean_enr / 100 * data.relative_qtys[rxtr][commod]])
    assert_array_almost_equal(r.group.cap_dirs, [True, True])
    assert_almost_equal(r.group.qty, data.sup_rhs[kind])

    # repo requester
    kind = data.Supports.repo
    r = spmod.Requester(kind, gids, nids)
    assert_equal(r.kind, kind)
    assert_equal(len(r.nodes), len(data.sup_pref_basis[kind].keys()))
    assert_equal(len(r.commod_to_nodes.values()), 
                 len(data.sup_pref_basis[kind].keys()))
    assert_equal(len(r.group.caps), 1)
    assert_array_almost_equal(r.group.caps, [data.sup_rhs[kind]])
    assert_almost_equal(r.group.qty, data.sup_rhs[kind])

def test_rqr_coeff():
    p = spmod.Point({'d_th': [0.7, 0.2, 0.1]})
    gids = cyctools.Incrementer()
    nids = cyctools.Incrementer()    
    kind = data.Supports.f_mox
    r = spmod.Requester(kind, gids, nids)

    enrs = [4.5, 62.5,
            62.5, 17.5,
            62.5, 17.5,]
    commods = [data.Commodities.uox, data.Commodities.th_mox,
               data.Commodities.f_mox, data.Commodities.uox,
               data.Commodities.f_thox, data.Commodities.uox,]
    rkinds = [data.Reactors.th, data.Reactors.th, 
              data.Reactors.f_mox, data.Reactors.f_mox, 
              data.Reactors.f_thox, data.Reactors.f_thox,]
    for i in range(len(enrs)):
        enr, commod, rkind = enrs[i], commods[i], rkinds[i]
        obs = r.coeff(enr, rkind, commod)
        exp = enr / 100 * data.relative_qtys[rkind][commod]

def test_reactor():
    p = spmod.Point({'f_rxtr': 1})
    kind = data.Reactors.f_mox
    r = spmod.Reactor(kind, p)
    assem_qty = data.core_vol_frac[kind] * data.fuel_unit / \
        data.n_assemblies[kind]
    
    # assembly groups
    gid = 5
    obs = r.gen_group(gid)
    exp = exinst.ExGroup(gid, False, [assem_qty], [False])
    assert_cyc_equal(obs, exp)

    # assembly node
    nid = 4
    excl_id = 2
    obs = r.gen_node(nid, gid, excl_id)
    exp = exinst.ExNode(nid, gid, False, assem_qty, True, excl_id)
    assert_cyc_equal(obs, exp)
        
def test_arc():
    aid, vid = 42, 52
    p = spmod.Point({'f_loc': 0})
    commod = data.Commodities.f_thox

    kind = data.Reactors.f_thox
    rxtr = spmod.Reactor(kind, p)

    gids = cyctools.Incrementer()
    nids = cyctools.Incrementer()    
    
    kinds = [data.Supports.f_thox, data.Supports.repo,]
    uids = [1, 4 + 1] # commod index of sup_pref_basis
    ucaps = [[1., rxtr.enr(commod) / 100 * data.relative_qtys[rxtr.kind][commod]],
             [1.],]
    print(len(kinds), len(uids), len(ucaps))
    for i in range(len(kinds)):
        print(len(kinds), len(uids), len(ucaps))
        uid, kind, caps = uids[i], kinds[i], ucaps[i]
        reqr = spmod.Requester(kind, gids, nids)    
        obs = spmod.StructuredSupply.gen_arc(aid, p, commod, vid, rxtr, reqr)
        exp = exinst.ExArc(aid, 
                           uid, caps, 
                           vid, [1], 
                           data.sup_pref_basis[kind][commod])
        assert_cyc_equal(obs, exp)
    
def test_primary_consumer_supplier():
    # This test confirms that for each primary supplier and consumer, a single
    # arcs is satisfied. This test does *not* check for the repository (see
    # below).
    #
    # Additionally, this test confirms that a round trip from run control file
    # to expected flows.

    fname = 'structured_supply_conv.py'
    base = os.path.dirname(os.path.abspath(__file__))
    fpath = os.path.join(base, 'files', fname)

    sp = spmod.StructuredSupply()
    fam = ResourceExchange()
    rc = cyctools.parse_rc(fpath)

    sp.read_space(rc._dict)
    assert_equal(sp.n_points, 1)
    for point in sp.points(): # there should only be one
        groups, nodes, arcs = sp.gen_inst(point)

    # 4 req groups, 3 rxtr groups
    assert_equal(len(groups), 4 + 3)
    # 12 req nodes, 3 from thermal and fmox, 2 from thox
    n_rq_nodes = sum((len(x) for x in data.sup_pref_basis.values()))   
    assert_equal(len(nodes), n_rq_nodes + 3 * 2 + 2) 
    # 3 arcs to thermal and fmox, 2 to thox
    assert_equal(len(arcs), 3 * 2 + 2)

    rxtr_to_commod = {
        data.Reactors.th: data.Commodities.th_mox,
        data.Reactors.f_mox: data.Commodities.f_mox,
        data.Reactors.f_thox: data.Commodities.f_thox,
        }

    obs_prefs = [a.pref for a in arcs]
    exp_prefs = []
    for rkind in sp._rlztn.n_rxtrs.keys():
        commod = rxtr_to_commod[rkind]
        for rq_kind in sp.commod_to_reqrs[commod]:
            exp_prefs.append(data.sup_pref_basis[rq_kind][commod])
    assert_equal(obs_prefs, exp_prefs)

    solver = Solver('cbc')
    soln = fam.run_inst((groups, nodes, arcs), solver)
    
    print('flows:', soln.flows)
    assert_equal(len(soln.flows), len(arcs))
    assert_almost_equal(soln.flows[0], 17500) # thmox from thermal reactors
    assert_almost_equal(soln.flows[4], 1400) # fmox from fmox reactors
    assert_almost_equal(soln.flows[6], 1400) # fthox from fthox reactors
    assert_almost_equal(sum(soln.flows.values()), 17500 + 1400 * 2)

def test_rlztn_reset():
    sp = spmod.StructuredSupply()
    fam = ResourceExchange()
    one_rxtr_exp = 1
    other_rxtr_exp = 42

    point = spmod.Point()
    _ = sp.gen_inst(point)
    r1 = sp._rlztn
    assert_equal(one_rxtr_exp, r1.n_rxtrs[0])
    
    _ = sp.gen_inst(point)
    r2 = sp._rlztn
    print('r1', r1.n_rxtrs)
    assert_equal(one_rxtr_exp, r2.n_rxtrs[0])
    point = spmod.Point({'n_rxtr': 42})
    
    _ = sp.gen_inst(point, reset_rlztn=False)
    r3 = sp._rlztn
    assert_equal(one_rxtr_exp, r3.n_rxtrs[0]) # the original bug
    
    point = spmod.Point()
    _ = sp.gen_inst(point)
    r4 = sp._rlztn
    assert_equal(one_rxtr_exp, r4.n_rxtrs[0])
    
    point = spmod.Point({'n_rxtr': 42})
    _ = sp.gen_inst(point)
    r5 = sp._rlztn
    print('r5', r5.n_rxtrs)
    assert_equal(other_rxtr_exp, r5.n_rxtrs[0]) # bug fixed
    
def test_repository_run():
    # This test confirms that flows to a constrainted repository behave as
    # expected.
    #
    # Because reactor core sizes are determined via the data module, the number
    # of reactors must be increased to reach capacity; however, multiple
    # assembly behavior is also tested.
    sp = spmod.StructuredSupply()
    fam = ResourceExchange()
    point = spmod.Point()
    
    # info for this test
    rx_kind = data.Reactors.th
    assem_per_rxtr = data.n_assemblies[rx_kind]
    mass_per_assem = data.fuel_unit * data.core_vol_frac[rx_kind] \
        / assem_per_rxtr    
    ## this is ceil because requesters *demand* fuel, i.e., are not constrained
    ## by it
    n_assem_for_repo = int(math.ceil(data.sup_rhs[data.Supports.repo] \
                                         / mass_per_assem))
    n_rxtrs = n_assem_for_repo / assem_per_rxtr + 1 # explicit int div
    print('mass per assem', mass_per_assem)
    print('assems per rxtr', assem_per_rxtr)
    print('n for repo', n_assem_for_repo)
    print('n rxtrs', n_rxtrs)

    # instance realization
    reqrs = {data.Supports.repo: 1}
    rxtrs = {rx_kind: n_rxtrs}
    dists = {rx_kind: {data.Commodities.th_mox: assem_per_rxtr}}
    keys = ['n_reqrs', 'n_rxtrs', 'assem_dists']
    sp._rlztn = namedtuple('Realization', keys)(reqrs, rxtrs, dists)
    groups, nodes, arcs = sp.gen_inst(point, reset_rlztn=False)

    # 1 req groups, nassems rxtr groups
    assert_equal(len(groups), 1 + n_rxtrs * assem_per_rxtr)
    # 4 req nodes, 2 * n_assems rxtr nodes
    assert_equal(len(nodes), 4 + n_rxtrs * assem_per_rxtr) 
    # arcs = rxtr nodes
    assert_equal(len(arcs), n_rxtrs * assem_per_rxtr)
    solver = Solver('cbc')
    soln = fam.run_inst((groups, nodes, arcs), solver)

    # flow testing (a little overkill, maybe)
    assert_equal(len(soln.flows), len(arcs))
    non_zero_flows = [x for _, x in soln.flows.items() if x > 0]
    for i in range(len(non_zero_flows)):
        assert_almost_equal(non_zero_flows[i], mass_per_assem)
    assert_equal(len(non_zero_flows), n_assem_for_repo)
    assert_almost_equal(sum(soln.flows.values()), n_assem_for_repo * mass_per_assem)

def test_fiss_constrained_run():
    # This test confirms that demand specified by the fissile content behaves as
    # expected.
    #
    # First a seed that returns smaller that 0.5 for a sufficient number of
    # entries in a row is determined in order to select the appropriate
    # enrichment level for each reactor (i.e., fissile content is less than the
    # average expected, required more batches). Then the exchange is run,
    # expecting an excess flow.
    sp = spmod.StructuredSupply()
    fam = ResourceExchange()
    
    # info for this test
    rx_kind = data.Reactors.f_mox
    rq_kind = data.Supports.f_mox
    c_kind = data.Commodities.f_mox
    mass_per_rxtr = data.fuel_unit * data.core_vol_frac[rx_kind]
    ## this is ceil because requesters *demand* fuel, i.e., are not constrained
    ## by it
    n_rxtrs_for_qty = int(math.ceil(data.sup_rhs[rq_kind] / mass_per_rxtr))
    
    # find seed where first n reactors is less than average
    n = n_rxtrs_for_qty
    avg = 1.
    seed = 0
    # 0.4 is used rather than 0.5 because a "close" lhs was still succeeding due
    # to rounding errors (likely in cbc)
    while avg >= 0.4:  
        seed += 1
        random.seed(seed)
        # skip every second entry, because random.random is called for enr_rnd
        # then loc (in that order)
        avg = sum([random.random() for i in range(2 * n)][::2]) / n

    point = spmod.Point({'seed': seed, 'f_fc': 1})
    n_rxtrs = n_rxtrs_for_qty + 1
    print('seed', seed, 'avg', avg)
    print('n for qty', n_rxtrs_for_qty)
    print('mass per rxtr', mass_per_rxtr)
    print('n rxtrs', n_rxtrs)

    # instance realization
    reqrs = {rq_kind: 1}
    rxtrs = {rx_kind: n_rxtrs}
    dists = {rx_kind: {c_kind: 1}}
    keys = ['n_reqrs', 'n_rxtrs', 'assem_dists']
    sp._rlztn = namedtuple('Realization', keys)(reqrs, rxtrs, dists)
    groups, nodes, arcs = sp.gen_inst(point, reset_rlztn=False)

    # 1 req groups, 1 group per rxtr
    assert_equal(len(groups), 1 + n_rxtrs)
    # 3 req nodes, 1 node per rxtr
    assert_equal(len(nodes), 3 + n_rxtrs)
    # arcs = rxtr nodes
    assert_equal(len(arcs), n_rxtrs)
    
    rhs = [data.sup_rhs[rq_kind],
           data.sup_rhs[rq_kind] * strtools.mean_enr(rx_kind, c_kind) / 100 \
               * data.relative_qtys[rx_kind][c_kind]]
    lhs = [[sum([mass_per_rxtr * x.ucaps[i] for x in arcs[:-1]])] for i in range(2)]
    print('rhs', rhs, 'lhs', lhs)       
    # check qty demand
    assert_greater(lhs[0], rhs[0])
    # check fiss demand
    assert_less(lhs[1], rhs[1])
    
    solver = Solver('cbc')
    soln = fam.run_inst((groups, nodes, arcs), solver)

    # flow testing
    assert_almost_equal(sum(soln.flows.values()), n_rxtrs * mass_per_rxtr)
    # currently fails for either cbc or greedy
