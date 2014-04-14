from cyclopts.tools import report, combine

from cyclopts.execute import GraphParams, SolverParams, Solution, \
    ArcFlow, execute_exchange
from cyclopts.params import Incrementer, Param, BoolParam, \
    ReactorRequestSampler, ReactorRequestBuilder

import shutil
import os
import uuid
import nose
import tables as t
from nose.tools import assert_equal, assert_true, assert_false

def test_report():
    db_path = os.path.join(os.getcwd(), str(uuid.uuid4()) + '.h5')
    
    sampler = ReactorRequestSampler()
    sp = SolverParams()
    gp = GraphParams()
    b = ReactorRequestBuilder(sampler, gp)
    b.build()
    soln = execute_exchange(gp, sp)
    for i in range(len(soln.flows)):
        f = ArcFlow(soln.flows[i:])
        print("obj:", f.id, gp.arc_pref[f.id] * f.flow)
    report(sampler, gp, sp, soln, db_path=db_path)

    if os.path.exists(db_path):
        os.remove(db_path)

def test_combine():    
    db1 = '994c5721-311d-46f3-8b7d-742beeaa9ec1.h5'
    db2 = 'e5b781e6-fb86-4099-a46b-f36370bf8af4.h5'
    db1 = os.path.join(os.getcwd(), 'dbs', db1)
    db2 = os.path.join(os.getcwd(), 'dbs', db2)
    
    new_file = os.path.join(os.getcwd(), 'dbs', 'combine.h5')
    copy_file = os.path.join(os.getcwd(), 'dbs', 'copy.h5')
    tmps = [new_file, copy_file]
    for tmp in tmps:
        if os.path.exists(tmp):
            os.remove(tmp)
    shutil.copyfile(db1, copy_file)
    
    combine([db1, db2], new_file=new_file)
    test = t.open_file(new_file, 'r')
    assert_equal(len(test.root.flows), 2)
    test.close()

    combine([copy_file, db2])
    test = t.open_file(copy_file, 'r')
    assert_equal(len(test.root.flows), 2)
    test.close()
    
    for tmp in tmps:
        if os.path.exists(tmp):
            os.remove(tmp)
