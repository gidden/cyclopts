import cyclopts.inst_io as iio

from cyclopts.instance import ExGroup, ExNode, ExArc 
from cyclopts.inst_io import xdvars

import numpy as np
from numpy.testing import assert_array_equal
import nose
from nose.tools import assert_equal
from collections import Iterable
import uuid
import tables as t
import os

# equality comparison is required on the python level because xdress can't
# currently wrap dunder magic, see 
# https://github.com/xdress/xdress/issues/46
def assert_xd_equal(exp, obs):
    assert_array_equal(xdvars(exp), xdvars(obs))
    for var in xdvars(exp):
        vexp = getattr(exp, var)
        vobs = getattr(obs, var)
        if isinstance(vexp, Iterable):
            assert_array_equal(vexp, vobs)
        else:
            assert_equal(vexp, vobs)

class TestExchangeIO:
    def setUp(self):
        self.instid = uuid.uuid4()
        self.tmp = "tmp_{0}".format(self.instid)
        self.h5file = t.open_file(self.tmp, mode='w',)
        self.h5node = self.h5file.root
        iio.check_extables(self.h5file, self.h5node)
        
    def tearDown(self):
        self.h5file.close()
        os.remove(self.tmp)

    def test_exgroup(self):
        exp = [ExGroup(1, True, np.array([1], dtype='float'), 3), 
               ExGroup(6, False, np.array([2, 3.5], dtype='float'))]
        iio.write_exobjs(self.h5node, self.instid, exp)
        obs = iio.read_exobjs(self.h5node, self.instid, ExGroup)
        assert_equal(len(exp), len(obs))
        for i in range(len(exp)):
            assert_xd_equal(exp[i], obs[i])

    def test_exnode(self):
        exp = [ExNode(1, 2, True, 3), 
               ExNode(6, 7, False, 0, True, 1)]
        iio.write_exobjs(self.h5node, self.instid, exp)
        obs = iio.read_exobjs(self.h5node, self.instid, ExNode)
        assert_equal(len(exp), len(obs))
        for i in range(len(exp)):
            assert_xd_equal(exp[i], obs[i])

    def test_exarc(self):
        exp = [ExArc(2, 1, np.array([1, 0.9, 4], dtype='float'), 
                     16, np.array([.295e-9], dtype='float'), 0.5e-10),
               ExArc(1, 32, np.array([8.1, 5.3e6], dtype='float'), 
                     5, np.array([0.1, 77, 47], dtype='float'), 0.5e10)]
        iio.write_exobjs(self.h5node, self.instid, exp)
        obs = iio.read_exobjs(self.h5node, self.instid, ExArc)
        assert_equal(len(exp), len(obs))
        for i in range(len(exp)):
            assert_xd_equal(exp[i], obs[i])
