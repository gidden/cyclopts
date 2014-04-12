"""Provides some useful tools for working with Cyclopts, including reporting
output.

:author: Matthew Gidden <matthew.gidden@gmail.com>
"""

import os
import uuid
import tables as t
import numpy as np

from cyclopts.execute import ArcFlow

class SolnDesc(t.IsDescription):
    sim_id = t.StringCol(36) # len(str(uuid.uuid4())) == 36
    arc_id = t.Int64Col()
    flow = t.Float64Col()

class Describer(object):
    
    def describe_flows(self, row, sim_id, flows):
        for f in flows:
            row['sim_id'] = str(sim_id)
            row['arc_id'] = f.id
            row['flow'] = f.flow
            
def report(gparams, sparams, soln, sim_id = None, db_path = None):
    """Dumps parameter and solution information to an HDF5 database.
    
    Parameters
    ----------
    gparams : cyclopts.execute.GraphParams
        ExchangeGraph-defining parameters
    sparams : cyclopts.execute.SolverParams
        ExchangeSolver-defining parameters
    soln : cyclopts.execute.Solution
        The solved graph's solution.
    sim_id : int, optional
        The simulation id to use in the database. A UUID is generated by 
        default.
    db_path : os.path or similar, optional
        The database to dump information to. The default is cyclopts.h5 
        file placed in the current working directory.
    """
    db_path = os.path.join(os.getcwd(), 'cyclopts.h5') if db_path is None \
        else db_path
    sim_id = uuid.uuid4().int if sim_id is None else sim_id

    mode = "a" if os.path.exists(db_path) else "w"
    h5file = t.open_file(db_path, mode=mode, title="Cyclopts Output")
    
    flows = [ArcFlow(soln.flows[i:]) for i in range(len(soln.flows))]
    solnparams = [soln.time]

    tables = [('solver', SolnDesc, 'Solver Params', sparams),
              ('graph', SolnDesc, 'Graph Params', gparams),
              ('flows', SolnDesc, 'Arc Flows', flows),
              ('solution', SolnDesc, 'Solution Params', solnparams),
              ]
    
    d = Describer()
    for name, desc, title, data in tables:
        if not name in h5file.root._v_children:
            h5file.create_table("/", name, desc, title)
        if hasattr(d, 'describe_' + name):
            row = h5file.get_node('/' + name).row
            meth = getattr(d, 'describe_' + name)
            meth(row, sim_id, data)
            row.append()
        
    h5file.close()
