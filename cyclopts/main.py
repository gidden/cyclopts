"""The main entry point for running Cyclopts from the command line.
"""

from __future__ import print_function

import argparse

from cyclopts.tools import to_h5, exec_from_h5

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
    
    # and away we go!
    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
