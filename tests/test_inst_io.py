import cyclopts.inst_io as iio

from cyclopts.instance import ExGroup, ExNode, ExArc 
from cyclopts.inst_io import xdvars

import numpy as np
from numpy.testing import assert_array_equal
import nose
from nose.tools import assert_equal
from collections import Sequence

# equality comparison is required on the python level because xdress can't
# currently wrap dunder magic, see 
# https://github.com/xdress/xdress/issues/46
def assert_xd_equal(exp, obs):
    assert_array_equal(xdvars(exp), xdvars(obs))
    for var in xdvars(exp):
        vexp = getattr(exp, var)
        vobs = getattr(obs, var)
        if isinstance(exp, Sequence):
            assert_array_equal(vexp, vobs)
        else:
            assert_equal(vexp, vobs)

def test_exgroup():
    exp = ExGroup(1, False, np.array([1], dtype='float'), 3)
    obs = ExGroup(1, False, np.array([1], dtype='float'), 3)
    assert_xd_equal(exp, obs)

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
