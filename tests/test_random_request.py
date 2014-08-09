from cyclopts.exchange_species import RandomRequest
from cyclopts.exchange_family import ResourceExchange

import nose
from nose.tools import assert_equal

def test_basics():
    sp = RandomRequest()
    assert_equal(sp.name, 'RandomRequest')
