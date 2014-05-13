
import subprocess
import os
import uuid

import tables as t

from nose.tools import assert_equal

def test_cli():
    base = os.path.dirname(os.path.abspath(__file__))
    frc = os.path.join(base, 'files', 'obs_valid.rc')    
    fin = os.path.join(base, "tmp_{0}.h5".format(str(uuid.uuid4())))
    fout = os.path.join(base, "tmp_{0}.h5".format(str(uuid.uuid4())))

    cmd = "cyclopts convert -i {0} -o {1}".format(frc, fin)
    assert_equal(0, subprocess.call(cmd.split(), shell=(os.name == 'nt')))

    cmd = "cyclopts exec -i {0} -o {1}".format(fin, fout)
    assert_equal(0, subprocess.call(cmd.split(), shell=(os.name == 'nt')))

    if os.path.exists(fout):
        os.remove(fout)

    nvalid = 5 # visual confirmation of obs_valid.rc
    solvers = "clp greedy"
    cmd = "cyclopts exec --input={0} --output={1} --solvers {2}".format(
        fin, fout, solvers)
    assert_equal(0, subprocess.call(cmd.split(), shell=(os.name == 'nt')))

    f = t.open_file(fout, 'r')
    for tbl in f.root._f_walknodes(classname='Table'):
        if tbl._v_name == 'solver':
            assert_equal(nvalid * len(solvers.split()), tbl.nrows)
    f.close()

    if os.path.exists(fout):
        os.remove(fout)

    if os.path.exists(fin):
        os.remove(fin)
