from cyclopts.structured_species import data as data

from nose.tools import assert_equal, assert_almost_equal, assert_true, assert_false

import math

def test_region():
    assert_equal(data.region(0.42, n_reg=5), 2)
    assert_equal(data.region(0.42, n_reg=10), 4)
    assert_equal(data.region(0.72, n_reg=5), 3)
    assert_equal(data.region(0.72, n_reg=10), 7)

def test_pref():
    base, rloc, sloc, n_reg, ratio = 0.5, 0.42, 0.72, 5, 0.33
    
    fidelity = 0
    obs = data.preference(base, rloc, sloc, fidelity, ratio, n_reg)
    exp = base
    assert_equal(obs, exp)

    fidelity = 1
    obs = data.preference(base, rloc, sloc, fidelity, ratio, n_reg)
    exp = base + ratio * math.exp(-1)
    assert_almost_equal(obs, exp)

    fidelity = 2
    obs = data.preference(base, rloc, sloc, fidelity, ratio, n_reg)
    exp = base + ratio * (math.exp(-1) + math.exp(rloc - sloc)) / 2
    assert_almost_equal(obs, exp)
