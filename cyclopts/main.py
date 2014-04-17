"""The main entry point for running Cyclopts from the command line.
"""

from __future__ import print_function

import argparse
from cyclopts.run_control import RunControl, NotSpecified, parse_rc 

from cyclopts.tools import SamplerBuilder, report
from cyclopts.params import ReactorRequestBuilder
from cyclopts.execute import GraphParams, SolverParams, execute_exchange

import os

def main():
    """Entry point for Cyclopts runs."""
    parser = argparse.ArgumentParser("Cyclopts", add_help=False)
    parser.add_argument('--rc', default=NotSpecified, 
                        help="path to run control file")

    args = parser.parse_args()
    rc = parse_rc(args.rc)
  
    db_path = 'cyclopts.h5' if not hasattr(rc, 'outfile') else rc.outfile
    solvers = ['cbc'] if not hasattr(rc, 'solver') else rc.solver
    
    b = SamplerBuilder()
    samplers = b.build(rc)
    
    for sampler in samplers:
        for solver in solvers:
            rrb = ReactorRequestBuilder(sampler)
            gparams = rrb.build()
            sparams = SolverParams(solver)
            soln = execute_exchange(gparams, sparams)
            report(sampler, gparams, sparams, soln, db_path=db_path)
            
    

if __name__ == "__main__":
    main()
