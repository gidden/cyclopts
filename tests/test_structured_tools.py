from cyclopts.structured_species import tools

from nose.tools import assert_equal, assert_almost_equal, assert_true, assert_false

import math
import numpy as np

def test_region():
    assert_equal(tools.region(0.42, n_reg=5), 2)
    assert_equal(tools.region(0.42, n_reg=10), 4)
    assert_equal(tools.region(0.72, n_reg=5), 3)
    assert_equal(tools.region(0.72, n_reg=10), 7)

def test_pref():
    base, rloc, sloc, n_reg, ratio = 0.5, 0.42, 0.72, 5, 0.33
    
    fidelity = 0
    obs = tools.preference(base, rloc, sloc, fidelity, ratio, n_reg)
    exp = base
    assert_equal(obs, exp)

    fidelity = 1
    obs = tools.preference(base, rloc, sloc, fidelity, ratio, n_reg)
    exp = base + ratio * math.exp(-1)
    assert_almost_equal(obs, exp)

    fidelity = 2
    obs = tools.preference(base, rloc, sloc, fidelity, ratio, n_reg)
    exp = base + ratio * (math.exp(-1) + math.exp(rloc - sloc)) / 2
    assert_almost_equal(obs, exp)

def test_pnt():
    
    class Point(tools.Point):
        def __init__(self, d=None):
            super(Point, self).__init__(d)

        def _parameters(self):
            return {'a': tools.Param(1, np.int32), 
                    'b': tools.Param(2, np.int32)}

    p = Point()
    assert_equal(p.a, 1)
    assert_equal(p.b, 2)
    
    p = Point({'a': 3})
    assert_equal(p.a, 3)
    assert_equal(p.b, 2)
    
