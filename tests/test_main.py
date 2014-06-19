from cyclopts import main
from cyclopts import tools

import os
import shutil
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

  import tables as t
  h5f = t.open_file('cyclopts/tests/files/exp_instances.h5', 'r')
  h5n = h5f.root.Instances.ExchangeInstProperties
  for row in h5n.iterrows():
    print(uuid.UUID(bytes=row['instid']).hex, row['n_arcs'])

"""
exp_uuid_arcs = [
    ('4bee553ad2574923a0c19dcffa669bdd', 1),
    ('741bb3864b224f61a6cf9a9f910aa69a', 2),
    ('3ded701f631c4be8b02ba3297d3fa670', 3),
    ('bd04d68431f1475f9b9d373b069f8b12', 4),
    ('a07cd014e9564778a69ae2f6cdebe226', 2),
    ('9b3b7607f27a45a3ad0a404dcb29a8c5', 4),
    ('ef550c2f5a2148629b7fe7f57c7822d5', 6),
    ('6fb9e2d02e1d40e3a9a81a7a6513c69c', 8),
    ('dc806d20e3444043a4082f2f77ec0939', 3),
    ('b1d68e095ed842fe848c7594a6643727', 6),
    ('11eb0ab1078048d2be0ff7f88547bff5', 9),
    ('d826cd10ef2942fb811624fcee5815ee', 12),
    ('c16ad5c3ae4b4526b4864dbdc2eb7d8d', 4),
    ('c1ff845537f349cfa8a1559a715fd640', 8),
    ('078f6be90ece4b0f8d094028cbd0c22f', 12),
    ('e0a8221169784067b572ec00232169ce', 16),
    ]

def test_instids():
    base = os.path.dirname(os.path.abspath(__file__))
    pth = os.path.join(base, 'files', 'exp_instances.h5')
    h5file = t.open_file(pth, 'r')
    h5node = h5file.root.Instances
    
    rc = {}
    obs = main.collect_instids(h5node=h5node, rc=rc)
    exp = set(uuid.UUID(x[0]).bytes for x in exp_uuid_arcs)
    assert_equal(exp, obs)
    assert_equal(len(exp), len(exp_uuid_arcs))
    
    exp_uuid_hex = exp_uuid_arcs[0][0]
    rc = {'inst_ids': [exp_uuid_hex]}
    obs = main.collect_instids(h5node=h5node, rc=rc)
    exp = set([uuid.UUID(exp_uuid_hex).bytes])
    assert_equal(len(exp), len(obs))
    assert_equal(exp, obs)

    bounds = (3, 12)
    conds = ['n_arcs > {0}'.format(bounds[0]), '&', 
             'n_arcs < {0}'.format(bounds[1])]
    rc = {'inst_queries': {'ExchangeInstProperties': conds}}
    obs = main.collect_instids(h5node=h5node, rc=rc)
    exp = set(uuid.UUID(x[0]).bytes \
                  for x in exp_uuid_arcs \
                  if x[1] > bounds[0] and x[1] < bounds[1])
    assert_equal(exp, obs)
    h5file.close()

def test_exec():
    base = os.path.dirname(os.path.abspath(__file__))
    db = os.path.join(base, "tmp_{0}.h5".format(str(uuid.uuid4())))
    shutil.copy(os.path.join(base, 'files', 'exp_instances.h5'), db)
    ninst = len(exp_uuid_arcs)
    solvers = "greedy cbc"
    
    cmd = "cyclopts exec --db={0} --solvers {1}".format(db, solvers)
    assert_equal(0, subprocess.call(cmd.split(), shell=(os.name == 'nt')))
    h5file = t.open_file(db, 'r')
    h5node = h5file.root.Results.General
    assert_equal(h5node.nrows, ninst * len(solvers.split()))
    for row in h5node.iterrows():
        assert_true(row['objective'] > 0)
        assert_true(row['time'] > 0)
    h5file.close()

    uuid_hex = exp_uuid_arcs[0][0]
    newdb = os.path.join(base, "tmp_{0}.h5".format(str(uuid.uuid4())))
    cmd = "cyclopts exec --db={0} --instids {1} --outdb {2}".format(
        db, uuid_hex, newdb)
    print("executing: {0}".format(cmd))
    assert_equal(0, subprocess.call(cmd.split(), shell=(os.name == 'nt')))
    h5file = t.open_file(newdb, 'r')
    h5node = h5file.root.Results.General
    assert_equal(h5node.nrows, 1)
    for row in h5node.iterrows():
        assert_equal(row['instid'], uuid.UUID(uuid_hex).bytes)
    h5file.close()
    
    if os.path.exists(newdb):
        os.remove(newdb)

    if os.path.exists(db):
        os.remove(db)

condor_cmd = """
cyclopts condor --db={db} --instids {instids} --solvers {solvers} \
                --user {user} --localdir {localdir} --no-auth
"""

def test_condor():
    base = os.path.dirname(os.path.abspath(__file__))
    tstdir = os.path.join(base, 'tmp_{0}'.format(uuid.uuid4()))
    os.makedirs(tstdir)
    dbname = 'exp_instances.h5'

    db = os.path.join(base, 'files', dbname)
    solvers = "greedy cbc"
    instids = [x[0] for x in exp_uuid_arcs[:2]]
    user = "gidden"

    timeout = 30 # seconds
    cmd = condor_cmd.format(db=db, instids=" ".join(instids), 
                            solvers=solvers, user=user, localdir=tstdir) 
    rtncode = tools.run(cmd.split(), timeout=timeout, shell=(os.name == 'nt'))[0]
    if rtncode == -9:
        print("Process timed out.")
    assert_equal(0, rtncode)
    
    h5file = t.open_file(os.path.join(tstdir, dbname), 'r')
    h5node = h5file.root.Instances.ExchangeInstProperties
    assert_equal(h5node.nrows, len(instids) * len(solvers.split()))
    h5file.close()
    
    shutil.rmtree(tstdir)
    
def test_convert():
    base = os.path.dirname(os.path.abspath(__file__))
    rc = os.path.join(base, 'files', 'obs_valid.rc')    
    db = os.path.join(base, "tmp_{0}.h5".format(str(uuid.uuid4())))

    ninst = 2
    nvalid = 5 # visual confirmation of obs_valid.rc
    solvers = "greedy cbc"

    cmd = "cyclopts convert --rc {0} --db {1} -n {2}".format(rc, db, ninst)
    assert_equal(0, subprocess.call(cmd.split(), shell=(os.name == 'nt')))
    h5file = t.open_file(db, 'r')
    h5node = h5file.root.Instances.ExchangeInstProperties
    assert_equal(h5node.nrows, ninst * nvalid)
    h5file.close()

    if os.path.exists(db):
        os.remove(db)
