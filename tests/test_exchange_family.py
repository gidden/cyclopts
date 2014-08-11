from cyclopts.exchange_family import ResourceExchange
from cyclopts import exchange_family

import numpy as np
from numpy.testing import assert_array_equal
import nose
from nose.tools import assert_equal
import uuid
import tables as t
import os

import cyclopts.cyclopts_io as cycio
from cyclopts.exchange_instance import ExGroup, ExNode, ExArc, ExSolver
from cyclopts.params import Incrementer

from utils import assert_xd_equal

class TestExchangeIO:
    def setUp(self):
        self.fname = "tmp_{0}".format(uuid.uuid4())
        self.h5file = t.open_file(self.fname, mode='w',)
        
    def tearDown(self):
        self.h5file.close()
        os.remove(self.fname)

    def test_roundtrip(self):
        print('test file {0}'.format(self.fname))
        exp_groups = [ExGroup(1, True, np.array([1], dtype='float'), 3), 
                      ExGroup(6, False, np.array([2, 3.5], dtype='float'))]
        exp_nodes = [ExNode(1, 2, True, 3), 
                     ExNode(6, 7, False, 0, True, 1)]
        exp_arcs = [ExArc(2, 1, np.array([1, 0.9, 4], dtype='float'), 
                          6, np.array([.295e-9], dtype='float'), 0.5e-10),
                    ExArc(1, 6, np.array([8.1, 5.3e6], dtype='float'), 
                          1, np.array([0.1, 77, 47], dtype='float'), 0.5e10)]
        
        # setup
        fam = exchange_family.ResourceExchange()
        tbls = fam.register_tables(self.h5file, '')
        manager = cycio.TableManager(self.h5file, tbls)
        paramid, instid = uuid.uuid4(), uuid.uuid4()

        # work
        fam.record_inst((exp_groups, exp_nodes, exp_arcs), instid, paramid, 
                        manager.tables)
        manager.flush_tables()
        obs_groups, obs_nodes, obs_arcs = fam.read_inst(instid, 
                                                        manager.tables)

        # test
        assert_equal(len(exp_groups), len(obs_groups))
        for i in range(len(exp_groups)):
            assert_xd_equal(exp_groups[i], obs_groups[i])
        assert_equal(len(exp_nodes), len(obs_nodes))
        for i in range(len(exp_nodes)):
            assert_xd_equal(exp_nodes[i], obs_nodes[i])
        assert_equal(len(exp_arcs), len(obs_arcs))
        for i in range(len(exp_arcs)):
            assert_xd_equal(exp_arcs[i], obs_arcs[i])

        del manager

def test_basics():
    fam = ResourceExchange()
    assert_equal(fam.name, 'ResourceExchange')

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
def test_run():
    req = True
    bid = False
    excl = True
    
    gid = Incrementer()
    rg1 = ExGroup(gid.next(), req, np.array([1], dtype='float'), 1)
    rg2 = ExGroup(gid.next(), req, np.array([1.5], dtype='float'), 1.5)
    rg3 = ExGroup(gid.next(), req, np.array([1, 0.4], dtype='float'), 1)
    bg1 = ExGroup(gid.next(), bid, np.array([2], dtype='float'))
    bg2 = ExGroup(gid.next(), bid, np.array([1.5, 2], dtype='float'))
    bg3 = ExGroup(gid.next(), bid, np.array([1], dtype='float'))
    grps = [rg1, rg2, rg3, bg1, bg2, bg3]

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
    nodes = [r11, r21, r22, r31, b11, b21, b22, b31]

    # p3 > p2 > p1 > p4 > p5
    prefs = [1.0 / 2**i for i in range(5)]
    aid = Incrementer()
    a1 = ExArc(aid.next(), 
               r11.id, np.array([1], dtype='float'), 
               b11.id, np.array([1], dtype='float'),
               prefs[2])
    a2 = ExArc(aid.next(), 
               r11.id, np.array([1], dtype='float'), 
               b21.id, np.array([1, 1], dtype='float'),
               prefs[1])
    a3 = ExArc(aid.next(), 
               r21.id, np.array([1], dtype='float'), 
               b22.id, np.array([1, 1], dtype='float'),
               prefs[0])
    a4 = ExArc(aid.next(), 
               r22.id, np.array([1], dtype='float'), 
               b31.id, np.array([1], dtype='float'),
               prefs[3])
    a5 = ExArc(aid.next(), 
               r31.id, np.array([1, 1], dtype='float'), 
               b31.id, np.array([1], dtype='float'),
               prefs[4])
    arcs = [a1, a2, a3, a4, a5]
        
    stypes = ["cbc", "clp-e", "greedy"]
    exp_flows = {0: 1, 1: 0, 2: 1, 3: 0.5, 4: 0.5}
    for t in stypes:
        print("\nTesting with solver: {0}\n".format(t))
        solver = ExSolver(t)
        soln = ResourceExchange().run_inst((grps, nodes, arcs), solver)
        for id, flow in soln.flows.iteritems():
            assert_equal(exp_flows[id], flow)
