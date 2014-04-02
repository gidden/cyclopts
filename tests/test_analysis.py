from cyclopts import analysis

import nose
from nose.tools import assert_equal

def test_test():
    assert_equal(analysis.main(), 0)
