from __future__ import print_function

from cyclopts.instance import ExGroup, ExNode, ExArc, ExSolution, ExSolver, Run, Incr, IncrOne
from cyclopts.dtypes import xd_exgroup, xd_exnode, xd_exarc
from cyclopts.params import Incrementer

import numpy as np

import nose
from nose.tools import assert_equal, assert_true

def gprint(g):
    print(g.id, g.kind, g.caps, g.qty)

def aprint(a):
    print("unode: {0}, vnode: {1}\npref: {2}, flow: {3}".format(
            a.uid, a.vid, a.pref, a.flow))
    
def test_inst():
    req = True
    bid = False
    excl = True
    
    gid = Incrementer()
    # constraint for qty needed for cbc/clp and actual qty needed for greedy
    rg1 = ExGroup(gid.next(), req, np.array([1], dtype='float'), 1)
    rg2 = ExGroup(gid.next(), req, np.array([1.5], dtype='float'), 1.5)
    rg3 = ExGroup(gid.next(), req, np.array([1], dtype='float'), 1)
    bg1 = ExGroup(gid.next(), bid, np.array([2], dtype='float'))
    bg2 = ExGroup(gid.next(), bid, np.array([1], dtype='float'))
    bg3 = ExGroup(gid.next(), bid, np.array([1], dtype='float'))
    grps = np.array([rg1, rg2, rg3, bg1, bg2, bg3], dtype=ExGroup)
    for g in grps:
        gprint(g)
    
    nid = Incrementer()
    ex_grp_id = Incrementer(1)
    r11 = ExNode(nid.next(), rg1.id, req, 1, excl, ex_grp_id.next())
    r21 = ExNode(nid.next(), rg2.id, req, 1.5)
    r22 = ExNode(nid.next(), rg2.id, req, 1.5)
    r31 = ExNode(nid.next(), rg3.id, req, 1)
    b11 = ExNode(nid.next(), bg1.id, bid, 2)
    b21 = ExNode(nid.next(), bg2.id, bid, 1, excl, ex_grp_id.next())
    b22 = ExNode(nid.next(), bg2.id, bid, 1, excl, b21.excl_id)
    b31 = ExNode(nid.next(), bg3.id, bid, 1)
    nodes = np.array([r11, r21, r22, r31, b11, b21, b22, b31], dtype=ExNode)

    # p1 > p2 > p3 > p4 > p5
    p1 = 1.0 
    p2 = p1 / 2 
    p3 = p2 / 2
    p4 = p3 / 2
    p5 = p4 / 2
    a1 = ExArc(r11.id, np.array([1], dtype='float'), 
               b11.id, np.array([1], dtype='float'),
               p1)
    a2 = ExArc(r11.id, np.array([1], dtype='float'), 
               b21.id, np.array([1], dtype='float'),
               p2)
    a3 = ExArc(r21.id, np.array([1], dtype='float'), 
               b22.id, np.array([1], dtype='float'),
               p3)
    a4 = ExArc(r22.id, np.array([1], dtype='float'), 
               b31.id, np.array([1], dtype='float'),
               p4)
    a5 = ExArc(r31.id, np.array([1], dtype='float'), 
               b31.id, np.array([1], dtype='float'),
               p5)
    arcs = np.array([a1, a2, a3, a4, a5], dtype=ExArc)

    vaprint = np.vectorize(aprint)
    for a in arcs:
        aprint(a)
        
    stypes = ["cbc", "clp", "greedy"]
    for t in stypes:
        solver = ExSolver(t)
        soln = Run(grps, nodes, arcs, solver)

    print("time: {0}, version {1}".format(soln.time, soln.cyclus_version))
    for a in arcs:
        aprint(a)
            
    print("incrementing arcs")
    Incr(arcs)
    for a in arcs:
        aprint(a)
        IncrOne(a)
        aprint(a)
                
