
from cyclopts.problems import ProblemSpecies
from cyclopts.cyclopts_io import Table as cycTable
from cyclopts.exchange_family import ResourceExchange

class RandomRequest(ProblemSpecies):
    """@TODO"""

    def __init__(self):
        super(RandomRequest, self).__init__()

    @property
    def family(self):
        """Returns
        -------
        family : ResourceExchange
            An instance of this species' family
        """
        return ResourceExchange()

    @property
    def name(self):
        """Returns
        -------
        name : string
            The name of this species
        """
        return 'RandomRequest'

    def register_tables(self, h5file, prefix):
        """Derived classes must implement this function and return their list of
        tables
        
        Parameters
        ----------
        h5file : PyTables File
            the hdf5 file
        prefix : string
            the absolute path to the group for tables of this species

        Returns
        -------
        tables : list of cyclopts_io.Tables
            All tables that could be written to by this species.
        """
        pass

    def read_space(self, space_dict):
        """Derived classes must implement this function.

        Parameters
        ----------
        space_dict : dict
            A dictionary container resulting from the reading in of a run 
            control file
        """
        pass

    @property
    def n_points(self):
        """Derived classes must implement this function returning the number of
        points in its parameter space.
        
        Returns
        -------
        n : int
            The total number of points in the parameter space
        """
        pass
    
    def next_point(self):
        """Derived classes must implement this function returning a
        representation of a point in its parameter space to be used by other
        class member functions.
        
        Returns
        -------
        point : tuple or other
            A representation of a point in parameter space to be used by this 
            species
        """
        pass    

    def record_point(self, point, tables):
        """Derived classes must implement this function, recording information
        about a parameter point in the appropriate tables.
        
        Parameters
        ----------
        point : tuple or other
            A representation of a point in parameter space
        tables : list of cyclopts_io.Table
            The tables that can be written to
        """
        pass

    def gen_instance(self, point):
        """Derived classes must implement this function, returning a
        representation of a problem instance.
        
        Parameters
        ----------
        point : tuple or other
            A representation of a point in parameter space
           
        Returns
        -------
        inst : tuple or other
            A representation of a problem instance to be used by this species' 
            family
        """
        pass
