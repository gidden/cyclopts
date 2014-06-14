"""The main entry point for running Cyclopts from the command line.
"""

from __future__ import print_function

import argparse

from cyclopts.tools import to_h5, exec_from_h5
from cyclopts.condor import submit_dag
import cyclopts.params as params

def condor(args):
    submit_dag(args.user, args.host, args.indb, args.solvers, 
               args.dumpdir, args.outdb, args.clean, args.auth)

def convert(args):
    """Converts a contiguous dataspace as defined by an input run control file
    into problem instances in an HDF5 database. Each discrete point, as
    represented by a Sampler-type object is converted into a row in a table of
    the object's name, and each instance derived from data points is added to
    its relevant Instance data tables.
    """
    fin = args.input
    fout = args.output
    ninst = args.ninst
    samplers = params.SamplerBuilder().build(parse_rc(fin))
    filters = t.Filters(complevel=4)
    fout = t.open_file(fout, mode='a', filters=filters)

    d = defaultdict(list)
    for s in samplers:
        d[s.__class__.__name__].append(s)
    tbl_names = d.keys()
    grp_name = 'Instances'
    
    # create leaves
    tbls = fout.root._f_list_nodes(classname="Table")
    grps = fout.root._f_list_nodes(classname="Group")
    for name in tbl_names:
        if name in tbls:
            pass
        print("creating table {0}".format(name))
        inst = d[name][0]
        fout.create_table(fout.root, name, 
                          description=inst.describe_h5(), 
                          filters=filters)
    if grp_name not in grps:
        print("creating group {0}".format(grp_name))
        fout.create_group(fout.root, grp_name, filters=filters)
    
    # populate leaves
    for name in tbl_names:
        tbl = fout.root._f_get_child(name)
        row = tbl.row
        for s in d[name]:
            s.export_h5(row)
            row.append()
            inst_builder_ctor = s.inst_builder_ctor()
            builder = builder_ctor(s)
            h5node = fout.root._f_get_child(grp_name)
            for i in range(ninst):
                builder.build()
                builder.write(h5node)
        tbl.flush()
    fout.close()

def execute(args):
    print("solvers:", args.solvers)
    exec_from_h5(args.input, args.output, args.rc, args.solvers)

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
    inh = ("The run control file to use that defines a continguous parameter space.")
    conv_parser.add_argument('-i', '--input', dest='input', help=inh)
    outh = ("The HDF5 file to dump converted parameter space points to. "
            "This file can later be used an input to an execute run.")
    conv_parser.add_argument('-o', '--output', dest='output', help=outh)
    ninst = ("The number of problem instances to generate per point in "
             "parameter space.")
    conv_parser.add_argument('-n', '--ninstances', type=int, dest='ninst', 
                             help=ninst, default=1)

    # for runs
    exech = ("Executes a parameter sweep as defined "
             "by the input database and other command line arguments.")
    exec_parser = sp.add_parser('exec', help=exech)
    exec_parser.set_defaults(func=execute)
    inh = ("An HDF5 file that defines points in the parameter space to be run.")
    exec_parser.add_argument('-i', '--input', dest='input', help=inh)
    outh = ("An HDF5 file to which output will be provided.")
    exec_parser.add_argument('-o', '--output', dest='output', help=outh)
    solversh = ("A list of which solvers to use..")
    exec_parser.add_argument('--solvers', nargs='*', default=['cbc'], dest='solvers', 
                             help=solversh)    
    rch = ("The run control file, which allows idetification of a subset of input to run.")
    exec_parser.add_argument('--rc', default=None, dest='rc', help=rch)    
    
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
