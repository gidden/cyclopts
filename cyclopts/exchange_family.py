
from cyclopts.problems import ProblemFamily
from cyclopts.cyclopts_io import Table as cycTable

class ResourceExchange(ProblemFamily):
    """A class representing families of resource exchange problems."""

    def __init__(self):
        super(ResourceExchange, self).__init__()

    @property
    def name(self):
        """
        Returns
        -------
        name : string
            The name of this species
        """
        return 'ResourceExchange'

    def register_tables(self, h5file, prefix):
        """Derived classes must implement this function and return their list of
        tables
        
        Parameters
        ----------
        h5file : PyTables File
            the hdf5 file
        prefix : string
            the absolute path to the group for tables of this family

        Returns
        -------
        tables : list of cyclopts_io.Tables
            All tables that could be written to by this species.
        """
        pass

    def record_inst(self, inst, tables):
        """Derived classes must implement this function.
        
        Parameters
        ----------
        inst : tuple or other
            A representation of a problem instance
        tables : list of cyclopts_io.Table
            The tables that can be written to
        """
        pass

    def record_soln(self, inst, soln, tables):
        """Derived classes must implement this function to return a list of
        
        Parameters
        ----------
        inst : tuple or other
            A representation of a problem instance
        soln : ProbSolution or similar
            A representation of a problem solution
        tables : list of cyclopts_io.Table
            The tables that can be written to
        """
        pass

    def read_inst(self, uuid, tables):
        """Derived classes must implement this function to return a tuple
        instance structures that can be provided to the run_inst function.
          
        Parameters
        ----------
        uuid : uuid
            The uuid of the instance to read
        tables : list of cyclopts_io.Table
            The tables that can be written to

        Returns
        -------
        inst : tuple or other
            A representation of a problem instance
        """
        pass

    def run_inst(self, inst, solver):
        """Derived classes must implement this function to take a tuple instance
        structures provided by the exec_inst function and return a ProblemResult
        or similar object.
        
        Parameters
        ----------
        inst : tuple or other
            A representation of a problem instance
        solver : ProbSolver or similar
            A representation of a problem solver

        Returns
        -------
        soln : ProbSolution or similar
            A representation of a problem solution
        """
        pass
