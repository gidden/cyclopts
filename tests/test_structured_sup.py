from cyclopts.structured_species import supply as strsup

import uuid
import math
import os

from nose.tools import assert_equal, assert_almost_equal, assert_true, assert_false
from numpy.testing import assert_array_almost_equal

from cyclopts import tools
from cyclopts.exchange_family import ResourceExchange
from cyclopts.structured_species import data as data
from cyclopts.problems import Solver

def test_basics():
    sp = strsup.StructuredSupply()
    
    exp = 'StructuredSupply'
    obs = sp.name
    assert_equal(obs, exp)
    
    assert_true(isinstance(sp.family, ResourceExchange))
