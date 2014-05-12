"""The main entry point for running Cyclopts from the command line.
"""

from __future__ import print_function

import argparse

from cyclopts.tools import to_h5, exec_from_h5
from cyclopts.condor import submit_dag

def condor(args):
    submit_dag(args.user, args.host, args.dbname, args.solvers, args.dumpdir, args.cleanup)

def convert(args):
    to_h5(args.input, args.output)

def execute(args):
    exec_from_h5(args.input, args.output, args.solvers)

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
    condor_parser.add_argument('-i', '--input', dest='dbname', help=indbh,
                               default='in.h5')    
    dumph = ("The directory in which to place output.")
    condor_parser.add_argument('-d', '--dumpdir', dest='dumpdir', help=dumph,
                               default='run_results')      
    nocleanh = ("Do *not* clean up the submit node after.")
    condor_parser.add_argument('--no-clean', dest='clean', help=nocleanh,
                               action='store_false', default=True)    
    solversh = ("A list of which solvers to use on each run.")
    condor_parser.add_argument('--solvers', nargs='*', default=['cbc'], dest='solvers', 
                             help=solversh)    
    
    # and away we go!
    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
