"""The main entry point for running Cyclopts from the command line.
"""

from __future__ import print_function

from cyclopts.tools import SamplerBuilder, report
from cyclopts.params import ReactorRequestBuilder
from cyclopts.execute import GraphParams, SolverParams, execute_exchange

import os

def read_rcparams(lines):
    return {
        'n_request': [range(1, 5)],
        'n_supply': [range(1, 5)],
        }

def main():
    """
    - read in the rc file
    - construct rcparams for building
    - build all samplers
    - for each solver
        - for each sampler
            - execute exchange
            - report
    """
    # argparser to get rc file 
    
    # read in rc file

    # get outpath and rcparams and solvers
    
    lines = [] # change to read rc
    db_path = 'cyclopts.h5' # change to read rc
    solvers = ['cbc'] # change to read rc
    rcparams = read_rcparams(lines)

    b = SamplerBuilder()
    samplers = b.build(rcparams)
    
    for sampler in samplers:
        for solver in solvers:
            rrb = ReactorRequestBuilder(sampler)
            gparams = rrb.build()
            sparams = SolverParams(solver)
            soln = execute_exchange(gparams, sparams)
            report(sampler, gparams, sparams, soln, db_path=db_path)
            
    
    print("cwd:", os.getcwd())

if __name__ == "__main__":
    main()
