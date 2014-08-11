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
from cyclopts.exchange_instance import ExGroup, ExNode, ExArc
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
