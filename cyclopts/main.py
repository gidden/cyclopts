"""The main entry point for running Cyclopts from the command line.
"""

from __future__ import print_function

import argparse
import cPickle as pickle
import uuid
import io
from cyclopts.run_control import RunControl, NotSpecified, parse_rc 

import cyclopts.params
from cyclopts.tools import SamplerBuilder, report
from cyclopts.params import ReactorRequestBuilder
from cyclopts.execute import GraphParams, SolverParams, execute_exchange

import os

def main():
    """Entry point for Cyclopts runs."""
    parser = argparse.ArgumentParser("Cyclopts", add_help=False)
    parser.add_argument('--rc', default=NotSpecified, 
                        help="path to run control file")
    parser.add_argument('-d', action='store_true', dest='dump',
                        help="if declared, Cyclopts will read in the " + 
                        "parameter space and dump out many other rc files " + 
                        "as well as a listing of all files generated.")
    parser.add_argument('--samplers-per-file', default=0, 
                        help="if dumping samplers, how many to put in " + 
                        "each generated file.")
    
    args = parser.parse_args()
    rc = parse_rc(args.rc)
    dump = args.dump
    n_per_file = args.samplers_per_file
  
    db_path = 'cyclopts.h5' if not hasattr(rc, 'outfile') else rc.outfile
    solvers = ['cbc'] if not hasattr(rc, 'solvers') else rc.solvers
    
    samplers = [pickle.loads(sampler) for sampler in rc.samplers] \
        if hasattr(rc, 'samplers') else []
    b = SamplerBuilder()
    samplers += b.build(rc)
    
    if dump: 
        dump_samplers(samplers, n_per_file, db_path, solvers)
    else:
        # run(args)
        execute_cyclopts(samplers, solvers, db_path)

def run(args):
    fin = args.infile
    fout = args.outfile
    solvers = params.solvers
    samplers = []

    fin = t.open_file(fin, mode='r')
    tbls = fin.root._f_list_nodes(classname="Table")
    for tbl in tbls:
        if not hasattr(cyclopts.params, tbl._v_name):
            continue
        for row in tbl:
            inst = getattr(cyclopts.params, tbl._v_name)()
            inst.h5import(row)
            samplers.append(inst)
    fin.close()
    execute_cyclopts(samplers, solvers, db_path)

def convert(args):
    fin = args.infile
    fout = args.outfile
    samplers = SamplerBuilder().build(fin)

    fout = t.open_file(fout, mode='a')
    for s in samplers:
        name = s.__class__.__name__
        if name not in fin.root._f_list_nodes(classname="Table"):
            f.create_table(fin.root, name, s.h5describe(), name + " Table")
        row = fin.root._f_get_child(name).row
        s.h5export(row)
        row.append()
    fout.close()

def execute_cyclopts(samplers, solvers, db_path): 
    for sampler in samplers:
        for solver in solvers:
            rrb = ReactorRequestBuilder(sampler)
            gparams = rrb.build()
            sparams = SolverParams(solver)
            soln = execute_exchange(gparams, sparams)
            report(sampler, gparams, sparams, soln, db_path=db_path)
            
def dump_samplers(samplers, n_per_file):
    n_per_file = len(samplers) if n_per_file == 0 else n_per_file
    fnames = []
    while len(samplers) != 0:
        fname = str(uuid.uuid4()) + '.rc'
        while os.path.exists(fname):
            fname = uuid.uuid4() + '.rc' # don't overwrite anyone
        fnames.append(fname)
        n = 0
        with io.open(fname, 'w') as f:
            lines = u'samplers = ['
            while n != n_per_file: 
                s = pickle.dumps(samplers.pop())
                lines += '"' + s.replace('\n', '\\n') +  '",\n'
                n += 1
            lines += ']\n'
            lines += 'solvers = ' + str(solvers)
            lines += 'outfile = ' + db_path
            f.write(lines)
    with io.open('generated_rc_files', 'w') as f:
        lines = u'/n'.join(fnames)
        f.write(lines)

if __name__ == "__main__":
    main()
