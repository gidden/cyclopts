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

def test_exgroup():
    instid = uuid.uuid4()
    tmp = "tmp_{0}".format(instid)
    h5file = t.open_file(tmp, mode='w',)
    h5node = h5file.root
    iio.check_extables(h5file, h5node)
    exp = [ExGroup(1, True, np.array([1], dtype='float'), 3), 
           ExGroup(6, False, np.array([2, 3.5], dtype='float'))]
    iio.write_exgroups(h5node, instid, exp)
    obs = iio.read_exgroups(h5node, instid)
    assert_equal(len(exp), len(obs))
    for i in range(len(exp)):
        assert_xd_equal(exp[i], obs[i])
    h5file.close()
    os.remove(tmp)

def test_exnode():
    exp = ExNode(1, 2, False, 3)
    obs = ExNode(1, 2, False, 3)
    assert_xd_equal(exp, obs)

def test_exarc():
    exp = ExArc(1, 2, np.array([1], dtype='float'), 
                3, np.array([1], dtype='float'), 0.5)
    obs = ExArc(1, 2, np.array([1], dtype='float'), 
                3, np.array([1], dtype='float'), 0.5)
    assert_xd_equal(exp, obs)
