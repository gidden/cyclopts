from cyclopts import main

import os
import tables as t
import uuid
import subprocess
import numpy as np
from numpy.testing import assert_array_equal

import nose
from nose.tools import assert_equal, assert_true

"""this is a print out of uid hexs and their number of arcs taken from
cyclopts/tests/files/exp_instances.h5 on 6/15/14 via

.. code-block::

  h5f = t.open_file('cyclopts/tests/files/exp_instances.h5', 'r')
  h5n = h5f.root.Instances.ExchangeInstProperties
  for row in h5n.iterrows():
    print(uuid.UUID(bytes=row['instid']).hex, row['n_arcs'])

"""
exp_uuid_arcs = [
    ('31edfc5c35694c7682076b0a078aeecf', 1),
    ('7ecf4de100dd4055a533b8ab2f18382d', 2),
    ('39831aad8605406fbab4f413c34dacf9', 3),
    ('0bac9e09ad5e4eadaeef3073bfada831', 4),
    ('6f236710bc9d4abb879948e21252ab6c', 2),
    ('53945b0e579c4db7bc0b465fe5b8364a', 4),
    ('e882748326ce4c24892a6e74f7e843c0', 6),
    ('8b84536c28934202acc55d6009334bf5', 8),
    ('d00330c86cb345d098c0cd0e4288c01e', 3),
    ('a08b4114ccef4defb0323f81b390a27e', 6),
    ('affdbd2f7af04e8ca398607b9671e4e8', 9),
    ('9bc8868cd9ad45a0b953558c4e36c3ab', 12),
    ('ba99512e1da84cadbea0765f8b0fc0d7', 4),
    ('b5a51c4ae07d48aabf0fc7cd17df9e83', 8),
    ('6b654619b50941c0a1150b9e2b9c85b0', 12),
    ('b28d6eccfbd546c995341b50281f5c52', 16),
    ]

def test_instids():
    base = os.path.dirname(os.path.abspath(__file__))
    pth = os.path.join(base, 'files', 'exp_instances.h5')
    h5file = t.open_file(pth, 'r')
    h5node = h5file.root.Instances
    
    rc = {}
    obs = main.instids_from_rc(h5node, rc)
    exp = set(uuid.UUID(x[0]).bytes for x in exp_uuid_arcs)
    assert_equal(exp, obs)
    assert_equal(len(exp), len(exp_uuid_arcs))
    
    exp_uuid_hex = exp_uuid_arcs[0][0]
    rc = {'inst_ids': [exp_uuid_hex]}
    obs = main.instids_from_rc(h5node, rc)
    exp = set([uuid.UUID(exp_uuid_hex).bytes])
    assert_equal(exp, obs)

    bounds = (3, 12)
    conds = ['n_arcs > {0}'.format(bounds[0]), '&', 
             'n_arcs < {0}'.format(bounds[1])]
    rc = {'inst_queries': {'ExchangeInstProperties': conds}}
    obs = main.instids_from_rc(h5node, rc)
    exp = set(uuid.UUID(x[0]).bytes \
                  for x in exp_uuid_arcs \
                  if x[1] > bounds[0] and x[1] < bounds[1])
    assert_equal(exp, obs)

def test_cli():
    base = os.path.dirname(os.path.abspath(__file__))
    rc = os.path.join(base, 'files', 'obs_valid.rc')    
    db = os.path.join(base, "tmp_{0}.h5".format(str(uuid.uuid4())))

    ninst = 2
    nvalid = 5 # visual confirmation of obs_valid.rc
    solvers = "cbc greedy"

    cmd = "cyclopts convert --rc {0} --db {1} -n {2}".format(rc, db, ninst)
    assert_equal(0, subprocess.call(cmd.split(), shell=(os.name == 'nt')))
    h5file = t.open_file(db, 'r')
    h5node = h5file.root.Instances.ExchangeInstProperties
    assert_equal(h5node.nrows, ninst * nvalid)
    h5file.close()

    cmd = "cyclopts exec --db={0} --solvers {1}".format(db, solvers)
    assert_equal(0, subprocess.call(cmd.split(), shell=(os.name == 'nt')))
    h5file = t.open_file(db, 'r')
    h5node = h5file.root.Results.General
    assert_equal(h5node.nrows, ninst * nvalid * len(solvers.split()))
    h5file.close()

    if os.path.exists(db):
        os.remove(db)
