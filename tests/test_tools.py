from cyclopts.tools import report

import os
import nose
from nose.tools import assert_equal, assert_true, assert_false

def test_null_report():
    db_path = os.path.join(os.getcwd(), 'cyclopts_test_file.h5')
    assert_false(os.path.exists(db_path))
    report(None, None, None, db_path=db_path)
    assert_true(os.path.exists(db_path))
    os.remove(db_path)
