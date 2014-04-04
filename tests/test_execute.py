from cyclopts.execute import Params, execute_exchange
from cyclopts.dtypes import xd_arcflow

import numpy as np

import nose
from nose.tools import assert_equal

def test_null():
    exp = np.zeros(0, dtype=xd_arcflow)
    params = Params()
    # obs = execute_exchange(params)
    # assert_equal(exp, obs)
    execute_exchange(params)
