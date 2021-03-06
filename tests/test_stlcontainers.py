"""Tests the part of stlconverters that is accessible from Python."""
###################
###  WARNING!!! ###
###################
# This file has been autogenerated
from __future__ import print_function
from unittest import TestCase
import nose

from nose.tools import assert_equal, assert_not_equal, assert_raises, raises, \
    assert_almost_equal, assert_true, assert_false, assert_in

from numpy.testing import assert_array_equal, assert_array_almost_equal

import os
import numpy  as np
from collections import Container, Mapping

from cyclopts import stlcontainers


# Vector Int


# Vector Double










# MapIntDouble
def test_map_int_double():
    m = stlcontainers.MapIntDouble()
    uismap = isinstance(-65.5555, Mapping) 
    m[1] = 18
    m[42] = -65.5555
    import pprint
    pprint.pprint(m)
    assert_equal(len(m), 2)
    if uismap:
        for key, value in m[42].items():
            print(key, value, -65.5555[key])
            if isinstance(value, np.ndarray):
                assert_almost_equal(value, -65.5555[key])
            else:
                assert_equal(value, -65.5555[key])
    else:
        assert_almost_equal(m[42], -65.5555)

    m = stlcontainers.MapIntDouble({-65: 42.42, 18: 1.0})
    assert_equal(len(m), 2)
    if uismap:
        for key, value in m[-65].items():
            if isinstance(value, np.ndarray):
                print(key, value, 42.42[key])
                assert_almost_equal(value, 42.42[key])
            else:
                assert_equal(value, 42.42[key])
    else:
        assert_almost_equal(m[-65], 42.42)

    n = stlcontainers.MapIntDouble(m, False)
    assert_equal(len(n), 2)
    if uismap:
        for key, value in m[-65].items():
            if isinstance(value, np.ndarray):
                assert_almost_equal(value, 42.42[key])
            else:
                assert_equal(value, 42.42[key])
    else:
        assert_almost_equal(m[-65], 42.42)

    # points to the same underlying map
    n[42] = -65.5555
    if uismap:
        for key, value in m[42].items():
            if isinstance(value, np.ndarray):
                assert_almost_equal(value, -65.5555[key])
            else:
                assert_equal(value, -65.5555[key])
    else:
        assert_almost_equal(m[42], -65.5555)



# MapIntInt
def test_map_int_int():
    m = stlcontainers.MapIntInt()
    uismap = isinstance(-65, Mapping) 
    m[1] = 18
    m[42] = -65
    import pprint
    pprint.pprint(m)
    assert_equal(len(m), 2)
    if uismap:
        for key, value in m[42].items():
            print(key, value, -65[key])
            if isinstance(value, np.ndarray):
                assert_almost_equal(value, -65[key])
            else:
                assert_equal(value, -65[key])
    else:
        assert_almost_equal(m[42], -65)

    m = stlcontainers.MapIntInt({-65: 42, 18: 1})
    assert_equal(len(m), 2)
    if uismap:
        for key, value in m[-65].items():
            if isinstance(value, np.ndarray):
                print(key, value, 42[key])
                assert_almost_equal(value, 42[key])
            else:
                assert_equal(value, 42[key])
    else:
        assert_almost_equal(m[-65], 42)

    n = stlcontainers.MapIntInt(m, False)
    assert_equal(len(n), 2)
    if uismap:
        for key, value in m[-65].items():
            if isinstance(value, np.ndarray):
                assert_almost_equal(value, 42[key])
            else:
                assert_equal(value, 42[key])
    else:
        assert_almost_equal(m[-65], 42)

    # points to the same underlying map
    n[42] = -65
    if uismap:
        for key, value in m[42].items():
            if isinstance(value, np.ndarray):
                assert_almost_equal(value, -65[key])
            else:
                assert_equal(value, -65[key])
    else:
        assert_almost_equal(m[42], -65)



# MapIntBool
def test_map_int_bool():
    m = stlcontainers.MapIntBool()
    uismap = isinstance(False, Mapping) 
    m[1] = True
    m[42] = False
    import pprint
    pprint.pprint(m)
    assert_equal(len(m), 2)
    if uismap:
        for key, value in m[42].items():
            print(key, value, False[key])
            if isinstance(value, np.ndarray):
                assert_almost_equal(value, False[key])
            else:
                assert_equal(value, False[key])
    else:
        assert_almost_equal(m[42], False)

    m = stlcontainers.MapIntBool({-65: False, 18: True})
    assert_equal(len(m), 2)
    if uismap:
        for key, value in m[-65].items():
            if isinstance(value, np.ndarray):
                print(key, value, False[key])
                assert_almost_equal(value, False[key])
            else:
                assert_equal(value, False[key])
    else:
        assert_almost_equal(m[-65], False)

    n = stlcontainers.MapIntBool(m, False)
    assert_equal(len(n), 2)
    if uismap:
        for key, value in m[-65].items():
            if isinstance(value, np.ndarray):
                assert_almost_equal(value, False[key])
            else:
                assert_equal(value, False[key])
    else:
        assert_almost_equal(m[-65], False)

    # points to the same underlying map
    n[42] = False
    if uismap:
        for key, value in m[42].items():
            if isinstance(value, np.ndarray):
                assert_almost_equal(value, False[key])
            else:
                assert_equal(value, False[key])
    else:
        assert_almost_equal(m[42], False)



# MapIntVectorInt
def test_map_int_vector_int():
    m = stlcontainers.MapIntVectorInt()
    uismap = isinstance([1, -65, 1, -65], Mapping) 
    m[1] = [42, 18, 42, 18]
    m[42] = [1, -65, 1, -65]
    import pprint
    pprint.pprint(m)
    assert_equal(len(m), 2)
    if uismap:
        for key, value in m[42].items():
            print(key, value, [1, -65, 1, -65][key])
            if isinstance(value, np.ndarray):
                assert_array_almost_equal(value, [1, -65, 1, -65][key])
            else:
                assert_equal(value, [1, -65, 1, -65][key])
    else:
        assert_array_almost_equal(m[42], [1, -65, 1, -65])

    m = stlcontainers.MapIntVectorInt({-65: [18, -65, 42, 1], 18: [1, 42, -65, 18]})
    assert_equal(len(m), 2)
    if uismap:
        for key, value in m[-65].items():
            if isinstance(value, np.ndarray):
                print(key, value, [18, -65, 42, 1][key])
                assert_array_almost_equal(value, [18, -65, 42, 1][key])
            else:
                assert_equal(value, [18, -65, 42, 1][key])
    else:
        assert_array_almost_equal(m[-65], [18, -65, 42, 1])

    n = stlcontainers.MapIntVectorInt(m, False)
    assert_equal(len(n), 2)
    if uismap:
        for key, value in m[-65].items():
            if isinstance(value, np.ndarray):
                assert_array_almost_equal(value, [18, -65, 42, 1][key])
            else:
                assert_equal(value, [18, -65, 42, 1][key])
    else:
        assert_array_almost_equal(m[-65], [18, -65, 42, 1])

    # points to the same underlying map
    n[42] = [1, -65, 1, -65]
    if uismap:
        for key, value in m[42].items():
            if isinstance(value, np.ndarray):
                assert_array_almost_equal(value, [1, -65, 1, -65][key])
            else:
                assert_equal(value, [1, -65, 1, -65][key])
    else:
        assert_array_almost_equal(m[42], [1, -65, 1, -65])



# MapIntVectorDouble
def test_map_int_vector_double():
    m = stlcontainers.MapIntVectorDouble()
    uismap = isinstance([1.0, -65.5555, 1.0, -65.5555], Mapping) 
    m[1] = [42.42, 18, 42.42, 18]
    m[42] = [1.0, -65.5555, 1.0, -65.5555]
    import pprint
    pprint.pprint(m)
    assert_equal(len(m), 2)
    if uismap:
        for key, value in m[42].items():
            print(key, value, [1.0, -65.5555, 1.0, -65.5555][key])
            if isinstance(value, np.ndarray):
                assert_array_almost_equal(value, [1.0, -65.5555, 1.0, -65.5555][key])
            else:
                assert_equal(value, [1.0, -65.5555, 1.0, -65.5555][key])
    else:
        assert_array_almost_equal(m[42], [1.0, -65.5555, 1.0, -65.5555])

    m = stlcontainers.MapIntVectorDouble({-65: [18, -65.5555, 42.42, 1.0], 18: [1.0, 42.42, -65.5555, 18]})
    assert_equal(len(m), 2)
    if uismap:
        for key, value in m[-65].items():
            if isinstance(value, np.ndarray):
                print(key, value, [18, -65.5555, 42.42, 1.0][key])
                assert_array_almost_equal(value, [18, -65.5555, 42.42, 1.0][key])
            else:
                assert_equal(value, [18, -65.5555, 42.42, 1.0][key])
    else:
        assert_array_almost_equal(m[-65], [18, -65.5555, 42.42, 1.0])

    n = stlcontainers.MapIntVectorDouble(m, False)
    assert_equal(len(n), 2)
    if uismap:
        for key, value in m[-65].items():
            if isinstance(value, np.ndarray):
                assert_array_almost_equal(value, [18, -65.5555, 42.42, 1.0][key])
            else:
                assert_equal(value, [18, -65.5555, 42.42, 1.0][key])
    else:
        assert_array_almost_equal(m[-65], [18, -65.5555, 42.42, 1.0])

    # points to the same underlying map
    n[42] = [1.0, -65.5555, 1.0, -65.5555]
    if uismap:
        for key, value in m[42].items():
            if isinstance(value, np.ndarray):
                assert_array_almost_equal(value, [1.0, -65.5555, 1.0, -65.5555][key])
            else:
                assert_equal(value, [1.0, -65.5555, 1.0, -65.5555][key])
    else:
        assert_array_almost_equal(m[42], [1.0, -65.5555, 1.0, -65.5555])





# MapIntMapIntVectorDouble
def test_map_int_map_int_vector_double():
    m = stlcontainers.MapIntMapIntVectorDouble()
    uismap = isinstance({1: [1.0, 42.42, -65.5555, 18], -65: [1.0, -65.5555, 1.0, -65.5555]}, Mapping) 
    m[1] = {42: [18, -65.5555, 42.42, 1.0], 18: [42.42, 18, 42.42, 18]}
    m[42] = {1: [1.0, 42.42, -65.5555, 18], -65: [1.0, -65.5555, 1.0, -65.5555]}
    import pprint
    pprint.pprint(m)
    assert_equal(len(m), 2)
    if uismap:
        for key, value in m[42].items():
            print(key, value, {1: [1.0, 42.42, -65.5555, 18], -65: [1.0, -65.5555, 1.0, -65.5555]}[key])
            if isinstance(value, np.ndarray):
                assert_array_almost_equal(value, {1: [1.0, 42.42, -65.5555, 18], -65: [1.0, -65.5555, 1.0, -65.5555]}[key])
            else:
                assert_equal(value, {1: [1.0, 42.42, -65.5555, 18], -65: [1.0, -65.5555, 1.0, -65.5555]}[key])
    else:
        assert_array_almost_equal(m[42], {1: [1.0, 42.42, -65.5555, 18], -65: [1.0, -65.5555, 1.0, -65.5555]})

    m = stlcontainers.MapIntMapIntVectorDouble({-65: {1: [1.0, 42.42, -65.5555, 18], 18: [42.42, 18, 42.42, 18], 42: [18, -65.5555, 42.42, 1.0], -65: [1.0, -65.5555, 1.0, -65.5555]}, 18: {1: [1.0, 42.42, -65.5555, 18], 42: [18, -65.5555, 42.42, 1.0], 18: [42.42, 18, 42.42, 18], -65: [1.0, -65.5555, 1.0, -65.5555]}})
    assert_equal(len(m), 2)
    if uismap:
        for key, value in m[-65].items():
            if isinstance(value, np.ndarray):
                print(key, value, {1: [1.0, 42.42, -65.5555, 18], 18: [42.42, 18, 42.42, 18], 42: [18, -65.5555, 42.42, 1.0], -65: [1.0, -65.5555, 1.0, -65.5555]}[key])
                assert_array_almost_equal(value, {1: [1.0, 42.42, -65.5555, 18], 18: [42.42, 18, 42.42, 18], 42: [18, -65.5555, 42.42, 1.0], -65: [1.0, -65.5555, 1.0, -65.5555]}[key])
            else:
                assert_equal(value, {1: [1.0, 42.42, -65.5555, 18], 18: [42.42, 18, 42.42, 18], 42: [18, -65.5555, 42.42, 1.0], -65: [1.0, -65.5555, 1.0, -65.5555]}[key])
    else:
        assert_array_almost_equal(m[-65], {1: [1.0, 42.42, -65.5555, 18], 18: [42.42, 18, 42.42, 18], 42: [18, -65.5555, 42.42, 1.0], -65: [1.0, -65.5555, 1.0, -65.5555]})

    n = stlcontainers.MapIntMapIntVectorDouble(m, False)
    assert_equal(len(n), 2)
    if uismap:
        for key, value in m[-65].items():
            if isinstance(value, np.ndarray):
                assert_array_almost_equal(value, {1: [1.0, 42.42, -65.5555, 18], 18: [42.42, 18, 42.42, 18], 42: [18, -65.5555, 42.42, 1.0], -65: [1.0, -65.5555, 1.0, -65.5555]}[key])
            else:
                assert_equal(value, {1: [1.0, 42.42, -65.5555, 18], 18: [42.42, 18, 42.42, 18], 42: [18, -65.5555, 42.42, 1.0], -65: [1.0, -65.5555, 1.0, -65.5555]}[key])
    else:
        assert_array_almost_equal(m[-65], {1: [1.0, 42.42, -65.5555, 18], 18: [42.42, 18, 42.42, 18], 42: [18, -65.5555, 42.42, 1.0], -65: [1.0, -65.5555, 1.0, -65.5555]})

    # points to the same underlying map
    n[42] = {1: [1.0, 42.42, -65.5555, 18], -65: [1.0, -65.5555, 1.0, -65.5555]}
    if uismap:
        for key, value in m[42].items():
            if isinstance(value, np.ndarray):
                assert_array_almost_equal(value, {1: [1.0, 42.42, -65.5555, 18], -65: [1.0, -65.5555, 1.0, -65.5555]}[key])
            else:
                assert_equal(value, {1: [1.0, 42.42, -65.5555, 18], -65: [1.0, -65.5555, 1.0, -65.5555]}[key])
    else:
        assert_array_almost_equal(m[42], {1: [1.0, 42.42, -65.5555, 18], -65: [1.0, -65.5555, 1.0, -65.5555]})



# PairIntInt
def test_pair_int_int():
    from numpy.testing import assert_array_equal
    p = stlcontainers.PairIntInt()
    p[0] = 18
    p[1] = -65
    assert_array_equal(p[0], p.first)
    assert_array_equal(p[1], p.second)
    import pprint
    pprint.pprint(p)
    pprint.pprint(p[0])
    pprint.pprint(p[1])
    q = p
    assert_array_equal(p, q)
    
    import copy
    r = copy.copy(p)
    pprint.pprint(r)
    pprint.pprint(r[0])
    pprint.pprint(r.first)
    pprint.pprint(r[1])
    pprint.pprint(r.second)
    assert_array_equal(p.first, r.first)
    assert_array_equal(p.second, r.second)



if __name__ == '__main__':
    nose.run()
