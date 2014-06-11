from __future__ import print_function

from cyclopts.instance import ExGroup, ExNode, ExArc, ExSolution, ExSolver, Run
from cyclopts.params import Incrementer

import numpy as np

import nose
from nose.tools import assert_equal, assert_true

def gprint(g):
    print(g.id, g.kind, g.caps, g.qty)

def aprint(a):
    print("id: {id}, unode: {0}, vnode: {1}\npref: {2}, flow: {3}".format(
            a.uid, a.vid, a.pref, a.flow, id=a.id))

"""This tests all possible features of a resource exchange graph generated using
a Cyclopts instance:

#. request groups with one and more than one request
#. bid groups with one and more than one bid
#. exclusive and non-exclusive bids to an exclusive request
#. exclusive bid groupings
#. multiple bids for a single request
#. single bid to multiple requests

The graph structure tested is

.. image:: ../test_inst.svg

Each node group has a single constraint, and all unit capacities are equal to 1.

=======  ========
Group Constraints
-----------------
GId      Value
=======  ========
1        1
2        1.5
3        1
4        2
5        1
6        1
=======  ========
        
Each node has an associated maximum quantity

=======  ========
Node Quantities
-----------------
NId      Value
=======  ========
1        1
2        1.5
3        1.5
4        1
5        2
6        1
7        1
8        1
=======  ========

Nodes 1, 6, and 7 are exclusive with nodes 6 and 7 forming an exclusive bid
group (ie., only one can be matched).

Finally, preferences for arcs are ranked in the following order: 3, 2, 1, 4,
5. This ordering guarantees that the exclusive bid grouping capability is
tested, because arcs 3 and 2 correspond to nodes 6 and 7, and are of highest
rank.
"""   
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

    # p3 > p2 > p1 > p4 > p5
    prefs = [1.0 / 2**i for i in range(5)]
    aid = Incrementer()
    a1 = ExArc(aid.next(), 
               r11.id, np.array([1], dtype='float'), 
               b11.id, np.array([1], dtype='float'),
               prefs[2])
    a2 = ExArc(aid.next(), 
               r11.id, np.array([1], dtype='float'), 
               b21.id, np.array([1], dtype='float'),
               prefs[1])
    a3 = ExArc(aid.next(), 
               r21.id, np.array([1], dtype='float'), 
               b22.id, np.array([1], dtype='float'),
               prefs[0])
    a4 = ExArc(aid.next(), 
               r22.id, np.array([1], dtype='float'), 
               b31.id, np.array([1], dtype='float'),
               prefs[3])
    a5 = ExArc(aid.next(), 
               r31.id, np.array([1], dtype='float'), 
               b31.id, np.array([1], dtype='float'),
               prefs[4])
    arcs = np.array([a1, a2, a3, a4, a5], dtype=ExArc)
        
    stypes = ["cbc", "clp", "greedy"]
    exp_flows = {0: 1, 1: 0, 2: 1, 3: 0.5, 4: 0.5}
    for t in stypes:
        solver = ExSolver(t)
        soln = Run(grps, nodes, arcs, solver)
        for id, flow in soln.flows.iteritems():
            assert_equal(exp_flows[id], flow)                
