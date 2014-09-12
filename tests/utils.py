from numpy.testing import assert_array_equal
from nose.tools import assert_equal, assert_almost_equal, assert_true
from collections import Iterable

from functools import wraps
import errno
import os
import signal
import warnings

xdattrs = lambda obj: [x for x in obj.__class__.__dict__.keys() \
                           if not x.startswith('_')]

from cyclopts import tools
        
def assert_cyc_equal(exp, obs):
    assert_array_equal(tools.cyc_members(exp), tools.cyc_members(obs))
    for var in tools.cyc_members(exp):
        vexp = getattr(exp, var)
        vobs = getattr(obs, var)
        print("exp {0}: {1}".format(var, vexp))
        print("obs {0}: {1}".format(var, vobs))
        if isinstance(vexp, Iterable):
            assert_array_equal(vexp, vobs)
        else:
            assert_equal(vexp, vobs)

class TimeoutError(Exception):
    pass

def timeout(seconds=10, error_message=os.strerror(errno.ETIME)):
    def decorator(func):
        def _handle_timeout(signum, frame):
            raise TimeoutError(error_message)

        def wrapper(*args, **kwargs):
            signal.signal(signal.SIGALRM, _handle_timeout)
            signal.alarm(seconds)
            try:
                result = func(*args, **kwargs)
            finally:
                signal.alarm(0)
            return result

        return wraps(func)(wrapper)

    return decorator
