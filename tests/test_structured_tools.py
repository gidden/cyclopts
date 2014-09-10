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

def test_rxtr_breakdown():
    class Point(tools.Point):
        def __init__(self, d=None):
            super(Point, self).__init__(d)

        def _parameters(self):
            return {'n_rxtr': tools.Param(1, np.int32), 
                    'r_t_f': tools.Param(1., np.float32), 
                    'r_th_pu': tools.Param(1., np.float32),
                    'f_fc': tools.Param(1, np.int32)}
    
    d = {
        'n_rxtr': 101,
        'r_t_f': 0.23,
        'r_th_pu': 0.15,
        }

    d['f_fc'] = 0
    p = Point(d)    
    obs = tools.reactor_breakdown(p)
    exp = (101, 0, 0)
    assert_equal(obs, exp)

    d['f_fc'] = 1
    p = Point(d)    
    obs = tools.reactor_breakdown(p)
    exp = (23, 66 + 12, 0)
    assert_equal(obs, exp)

    d['f_fc'] = 2
    p = Point(d)    
    obs = tools.reactor_breakdown(p)
    exp = (23, 66, 12)
    assert_equal(obs, exp)

def test_sup_breakdown():
    parameters = {
        'n_rxtr': tools.Param(1, np.int32), 
        'r_t_f': tools.Param(1., np.float32), 
        'r_th_pu': tools.Param(1., np.float32),
        'r_s_th': tools.Param(1., np.float32),
        'r_s_mox_uox': tools.Param(1., np.float32),
        'r_s_mox': tools.Param(1., np.float32),
        'r_s_thox': tools.Param(1., np.float32),
        'f_fc': tools.Param(1, np.int32)
        }
    
    class Point(tools.Point):
        def __init__(self, d=None):
            super(Point, self).__init__(d)

        def _parameters(self):
            return parameters 

    d = {
        'n_rxtr': 101,
        'r_t_f': 0.23,
        'r_th_pu': 0.15,
        'r_s_th': 0.13,
        'r_s_mox_uox': 0.75,
        'r_s_mox': 0.45,
        'r_s_thox': 0.39,
        'r_repo': 0.5,
        }

    d['f_fc'] = 0
    p = Point(d)
    obs = tools.support_breakdown(p) 
    exp = (13, 0, 0, 0, 0)    
    assert_equal(obs, exp)

    d['f_fc'] = 1
    p = Point(d)
    obs = tools.support_breakdown(p) 
    exp = (2, 1, 35, 0, 0)    
    assert_equal(obs, exp)
    
    d['f_fc'] = 2
    p = Point(d)
    obs = tools.support_breakdown(p) 
    exp = (2, 1, 30, 5, 0)    
    assert_equal(obs, exp)

    # add repository to params
    parameters['r_repo'] = tools.Param(1., np.float32)

    d['f_fc'] = 0
    p = Point(d)
    assert_true(hasattr(p, 'r_repo'))
    obs = tools.support_breakdown(p) 
    exp = (13, 0, 0, 0, 7)    
    assert_equal(obs, exp)

    d['f_fc'] = 1
    p = Point(d)
    obs = tools.support_breakdown(p) 
    exp = (2, 1, 35, 0, 19)    
    assert_equal(obs, exp)
    
    d['f_fc'] = 2
    p = Point(d)
    obs = tools.support_breakdown(p) 
    exp = (2, 1, 30, 5, 19)    
    assert_equal(obs, exp)
    
    
