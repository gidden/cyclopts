from cyclopts.params import ReactorRequestSampler
from nose.tools import assert_equal, assert_true, assert_false

def test_default_rxtr_req():
    s = ReactorRequestSampler()
    assert_equal(1, s.n_commods.sample())
    assert_equal(1, s.n_request.sample())
    assert_equal(1, s.assem_per_req.sample())
    assert_equal(0, s.req_multi_frac.sample())
    assert_equal(1, s.req_multi_commods.sample())
    assert_false(s.exclusive.sample())
    assert_equal(0, s.n_req_constr.sample())
    assert_equal(1, s.n_supply.sample())
    assert_equal(0, s.sup_multi_frac.sample())
    assert_equal(1, s.sup_multi_commods.sample())
    assert_equal(1, s.n_sup_constr.sample())
    assert_equal(1, s.sup_constr_val.sample())
    assert_true(s.connection.sample())
