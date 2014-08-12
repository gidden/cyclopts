"""This module provides base classes for Problem Families, Species, and Instances.

:author: Matthew Gidden
"""

from cyclopts._cproblem import *

class ProblemFamily(object):
    """A class representing families of problems that share the same
    structure.
    """

    def __init__(self):
        pass

    @property
    def name(self):
        """Derived classes should implement this function, returning the name of
        the family
               
        Returns
        -------
        name : string
            The name of this family
        """
        raise NotImplementedError

    @property            
    def table_prefix(self):
        """Returns the HDF5 group location for tables of this family"""
        return '/{0}/{1}'.format('Family', self.name)

    @property            
    def property_table_name(self):
        """Derived classes must implement this function and return the name of
        the table associated with aggregate instance properties

        Returns
        -------
        name : string
            The name of this family's instance property table
        """
        raise NotImplementedError

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
        raise NotImplementedError

    def record_inst(self, inst, inst_uuid, param_uuid, tables):
        """Derived classes must implement this function.
        
        Parameters
        ----------
        inst : tuple or other
            A representation of a problem instance
        inst_uuid : uuid
            The uuid of the instance
        param_uuid : uuid
            The uuid of the point in parameter space
        tables : list of cyclopts_io.Table
            The tables that can be written to
        """
        raise NotImplementedError

    def record_soln(self, soln, soln_uuid, inst, inst_uuid, tables):
        """Derived classes must implement this function to return a list of
        
        Parameters
        ----------
        soln : ProbSolution or similar
            A representation of a problem solution
        soln_uuid : uuid
            The uuid of the solution
        inst : tuple or other
            A representation of a problem instance
        inst_uuid : uuid
            The uuid of the instance
        tables : list of cyclopts_io.Table
            The tables that can be written to
        """
        raise NotImplementedError

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
        raise NotImplementedError

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
        raise NotImplementedError

class ProblemSpecies(object):
    """A class represnting species of problems that share the same parameter
    space and ProblemFamiliy."""

    def __init__(self):
        pass

    @property
    def family(self):
        """Derived classes must implement this function and return and instance
        of this species' family
       
        Returns
        -------
        family : ProblemFamily or similar
            An instance of this species' family
        """
        raise NotImplementedError

    @property
    def name(self):
        """Derived classes should implement this function, returning the name of
        the species
               
        Returns
        -------
        name : string
            The name of this species
        """
        raise NotImplementedError

    @property            
    def table_prefix(self):
        """Returns the HDF5 group location for tables of this species"""
        return '/{0}/{1}'.format('Species', self.name)

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
        raise NotImplementedError

    def read_space(self, space_dict):
        """Derived classes must implement this function.

        Parameters
        ----------
        space_dict : dict
            A dictionary container resulting from the reading in of a run 
            control file
        """
        raise NotImplementedError

    @property
    def n_points(self):
        """Derived classes must implement this function returning the number of
        points in its parameter space.
        
        Returns
        -------
        n : int
            The total number of points in the parameter space
        """
        raise NotImplementedError
    
    def points(self):
        """Derived classes must implement this function returning a
        representation of a point in its parameter space to be used by other
        class member functions.
        
        Returns
        -------
        point_generator : generator
            A generator for representation of a point in parameter space to be 
            used by this species
        """
        raise NotImplementedError    

    def record_point(self, point, param_uuid, tables):
        """Derived classes must implement this function, recording information
        about a parameter point in the appropriate tables.
        
        Parameters
        ----------
        point : tuple or other
            A representation of a point in parameter space
        param_uuid : uuid
            The uuid of the point in parameter space
        tables : list of cyclopts_io.Table
            The tables that can be written to
        """
        raise NotImplementedError

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
        raise NotImplementedError
    
