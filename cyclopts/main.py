"""The main entry point for running Cyclopts from the command line.
"""

from __future__ import print_function

import argparse
import tables as t
import numpy as np
from collections import defaultdict
import itertools
import uuid

import cyclopts
import cyclopts.condor as condor
import cyclopts.tools as tools
import cyclopts.inst_io as iio
import cyclopts.instance as inst

_inst_grp_name = 'Instances'
_result_grp_name = 'Results'
_result_tbl_name = 'General'
_result_tbl_dtype = np.dtype([
        ("instid", ('str', 16)), # 16 bytes for uuid
        ("problem", ('str', 30)), # 30 seems long enough, right?
        ("solver", ('str', 30)), # 30 seems long enough, right?
        ("time", np.float64),
        ("objective", np.float64),
        ("cyclus_version", ('str', 12)),
        ("cyclopts_version", ('str', 12)),
        ])
_filters = t.Filters(complevel=4)

def condor(args):
    condor.submit_dag(args.user, args.host, args.indb, args.solvers, 
                      args.dumpdir, args.outdb, args.clean, args.auth)

def convert(args):
    """Converts a contiguous dataspace as defined by an input run control file
    into problem instances in an HDF5 database. Each discrete point, as
    represented by a Sampler-type object is converted into a row in a table of
    the object's name, and each instance derived from data points is added to
    its relevant Instance data tables.
    """
    fin = args.rc
    fout = args.db
    ninst = args.ninst
    samplers = tools.SamplerBuilder().build(tools.parse_rc(fin))
    h5file = t.open_file(fout, mode='a', filters=_filters)
    root = h5file.root

    d = defaultdict(list)
    for s in samplers:
        d[s.__class__.__name__].append(s)
    tbl_names = d.keys()
    
    # create leaves
    for name in tbl_names:
        if root.__contains__(name):
            continue
        print("creating table {0}".format(name))
        inst = d[name][0]
        h5file.create_table(root, name, 
                            description=inst.describe_h5(), 
                            filters=_filters)
    if not root.__contains__(_inst_grp_name):
        print("creating group {0}".format(_inst_grp_name))
        h5file.create_group(root, _inst_grp_name, filters=_filters)
    
    # populate leaves
    for name in tbl_names:
        tbl = root._f_get_child(name)
        row = tbl.row
        for s in d[name]:
            s.export_h5(row)
            row.append()
            inst_builder_ctor = s.inst_builder_ctor()
            builder = inst_builder_ctor(s)
            h5node = root._f_get_child(_inst_grp_name)
            for i in range(ninst):
                builder.build()
                builder.write(h5node)
        tbl.flush()
    h5file.close()

def instids_from_rc(h5node, rc):
    instids = set(uuid.UUID(x).bytes for x in rc['inst_ids']) \
        if 'inst_ids' in rc.keys() else set()
    
    # inst queries are a mapping from instance table names to queryable
    # conditions, the result of which is a collection of instids that meet those
    # conditions
    inst_queries = rc['inst_queries'] if 'inst_queries' in rc.keys() else {}
    for tbl_name, conds in inst_queries.items():
        tbl = h5node._f_get_child(tbl_name)
        ops = conds[1::2]
        conds = ['({0})'.format(c) if \
                     not c.lstrip().startswith('(') and \
                     not c.rstrip().endswith(')') else c for c in conds[::2]]
        cond = ' '.join(
                [' '.join(i) for i in \
                     itertools.izip_longest(conds, ops, fillvalue='')]).strip()
        rows = tbl.where(cond)
        for row in rows:
            instids.add(row['instid'])
        
    # if no ids, then run everything
    if len(instids) == 0:
        names = [node._v_name \
                     for node in h5node._f_iter_nodes(classname='Table') \
                     if 'properties' in node._v_name.lower()]
        for tbl_name in names:
            tbl = h5node._f_get_child(tbl_name)
            for row in tbl.iterrows():
                instids.add(row['instid'])
    
    return instids
    
def execute(args):
    db = args.db
    rc = parse_rc(args.rc) if args.rc is not None else {}
    solvers = args.solvers
    h5file = t.open_file(db, mode='a', filters=_filters)
    root = h5file.root
    instnode = root._f_get_child(_inst_grp_name)
    instids = instids_from_rc(instnode, rc)

    # create output leaves
    if not root.__contains__(_result_grp_name):
        print("creating group {0}".format(_result_grp_name))
        h5file.create_group(root, _result_grp_name, filters=_filters)
    resultnode = root._f_get_child(_result_grp_name)

    if not resultnode.__contains__(_result_tbl_name):
        h5file.create_table(resultnode, _result_tbl_name, _result_tbl_dtype, 
                            filters=_filters)    
    tbl = resultnode._f_get_child(_result_tbl_name) 

    # run each instance note that the running and reporting is specific to
    # exchange problems, and future problem instances will need this section to
    # be refactored
    row = tbl.row
    for id in instids:
        groups, nodes, arcs = iio.read_exinst(instnode, id) # exchange specific
        for s in solvers:
            solver = inst.ExSolver(s)
            soln = inst.Run(groups, nodes, arcs, solver) # exchange specific
            iio.write_soln(instnode, id, soln) # exchange specific
            row['instid'] = id
            row["solver"] = s
            row["problem"] = soln.type
            row["time"] = soln.time
            row["objective"] = soln.objective
            row["cyclus_version"] = soln.cyclus_version
            row["cyclopts_version"] = cyclopts.__version__
            row.append()
            tbl.flush()        
            
def main():
    """Entry point for Cyclopts runs."""
    parser = argparse.ArgumentParser("Cyclopts", add_help=True)    
    sp = parser.add_subparsers()

    # for conversion
    converth = ("Convert a parameter space defined by an "
                "input run control file into an HDF5 database for a Cyclopts "
                "execution run.")
    conv_parser = sp.add_parser('convert', help=converth)
    conv_parser.set_defaults(func=convert)
    rc = ("The run control file to use that defines a continguous parameter space.")
    conv_parser.add_argument('--rc', dest='rc', help=rc)
    db = ("The HDF5 file to dump converted parameter space points to. "
            "This file can later be used an input to an execute run.")
    conv_parser.add_argument('--db', dest='db', default='cyclopts.h5', help=db)
    ninst = ("The number of problem instances to generate per point in "
             "parameter space.")
    conv_parser.add_argument('-n', '--ninstances', type=int, dest='ninst', 
                             default=1, help=ninst)

    # for runs
    exech = ("Executes a parameter sweep as defined "
             "by the input database and other command line arguments.")
    exec_parser = sp.add_parser('exec', help=exech)
    exec_parser.set_defaults(func=execute)
    db = ("An HDF5 Cyclopts database (e.g., the result of 'cyclopts convert').")
    exec_parser.add_argument('--db', dest='db', help=db)
    solversh = ("A list of which solvers to use.")
    exec_parser.add_argument('--solvers', nargs='*', default=['cbc'], dest='solvers', 
                             help=solversh)    
    rch = ("The run control file, which allows idetification of a subset "
           "of input to run.")
    exec_parser.add_argument('--rc', dest='rc', default=None, help=rch)
    
    # for condor
    condorh = ("Submits a job to condor, retrieves output when it has completed, "
             "and cleans up the condor user space after.")
    condor_parser = sp.add_parser('condor', help=condorh)
    condor_parser.set_defaults(func=condor)
    
    uh = ("The condor user name.")
    condor_parser.add_argument('-u', '--user', dest='user', help=uh, 
                               default='gidden')
    hosth = ("The condor submit host.")
    condor_parser.add_argument('-t', '--host', dest='host', help=hosth, 
                               default='submit-1.chtc.wisc.edu')
    indbh = ("The input database.")
    condor_parser.add_argument('-i', '--input', dest='indb', help=indbh,
                               default='in.h5')    
    dumph = ("The directory in which to place output.")
    condor_parser.add_argument('-d', '--dumpdir', dest='dumpdir', help=dumph,
                               default='run_results')      
    outdbh = ("The output database.")
    condor_parser.add_argument('-o', '--output', dest='outdb', help=outdbh,
                               default='out.h5')    
    nocleanh = ("Do *not* clean up the submit node after.")
    condor_parser.add_argument('--no-clean', dest='clean', help=nocleanh,
                               action='store_false', default=True)    
    solversh = ("A list of which solvers to use on each run.")
    condor_parser.add_argument('--solvers', nargs='*', default=['cbc'], dest='solvers', 
                             help=solversh)
    noauthh = ("Do not ask for a password for authorization.")
    condor_parser.add_argument('--no-auth', action='store_false', dest='auth', 
                               default=True, help=noauthh)    
    
    # and away we go!
    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
