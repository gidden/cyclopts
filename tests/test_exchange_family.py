from cyclopts.exchange_family import ResourceExchange

import nose
from nose.tools import assert_equal

def test_basics():
    fam = ResourceExchange()
    assert_equal(fam.name, 'ResourceExchange')
