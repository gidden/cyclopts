"""This module provides base classes for Problem Families, Species, and Solvers.

:author: Matthew Gidden <matthew.gidden _at_ gmail.com>
"""

from cyclopts._cproblem import *

class ProblemFamily(object):
    """A class representing families of problems that share the same
    structure.
    """

    @property            
    def io_prefix(cls):
        """Returns the HDF5 group location for tables of this family"""
        return '/{0}/{1}'.format('Family', cls.name)

    @property
    def name(cls):
        """Derived classes should implement this function, returning the name of
        the family
               
        Returns
        -------
        name : string
            The name of this family
        """
        raise NotImplementedError

    @property            
    def property_table_name(cls):
        """Derived classes must implement this function and return the name of
        the table associated with aggregate instance properties

        Returns
        -------
        name : string
            The name of this family's instance property table
        """
        raise NotImplementedError

    def __init__(self):
        pass

    def register_groups(self, h5file, prefix):
        """Derived classes can implement this function and return their list of
        groups
        
        Parameters
        ----------
        h5file : PyTables File
            the hdf5 file
        prefix : string
            the absolute path to the group for tables of this species

        Returns
        -------
        groups : list of cyclopts_io.Groups
            All groups that could be written to by this species.
        """
        return []

    def register_tables(self, h5file, prefix):
        """Derived classes can implement this function and return their list of
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
        return []

    def record_inst(self, inst, inst_uuid, param_uuid, species, 
                    io_manager=None):
        """Derived classes must implement this function.
        
        Parameters
        ----------
        inst : tuple or other
            A representation of a problem instance
        inst_uuid : uuid
            The uuid of the instance
        param_uuid : uuid
            The uuid of the point in parameter space
        species : str
            The name of the species that generated this instance
        io_manager : cyclopts_io.IOManager, optional
            IOManager that gives access to tables/groups for writing
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

    def post_process(self, instid, solnids, tbls):
        """Derived classes can implement this function to output interesting
        aggregate data during a post-processing step after some number of
        instance executions.
        
        Parameters
        ----------
        instid : UUID 
            UUID of the instance to post process
        solnids : tuple of UUIDs
            a collection of solution UUIDs corresponding the instid 
        tbls : 3-tuple of cyclopts.cyclopts_io.Tables
            tables from an input file, tables from an output file,
            and tables from a post-processed file

        Returns
        -------
        props : tuple 
            tuple of number of arcs and mapping of solution UUIDs to numpy 
            arrays of arc flows
        """
        pass

class ProblemSpecies(object):
    """A class represnting species of problems that share the same parameter
    space and ProblemFamiliy."""

    @property
    def family(cls):
        """Derived classes must implement this function and return and instance
        of this species' family
       
        Returns
        -------
        family : ProblemFamily or similar
            An instance of this species' family
        """
        raise NotImplementedError

    @property
    def name(cls):
        """Derived classes should implement this function, returning the name of
        the species
               
        Returns
        -------
        name : string
            The name of this species
        """
        raise NotImplementedError

    @property            
    def io_prefix(cls):
        """Returns the HDF5 group location for tables of this species"""
        return '/{0}/{1}'.format('Species', cls.name)

    def __init__(self):
        pass

    def register_groups(self, h5file, prefix):
        """Derived classes can implement this function and return their list of
        groups
        
        Parameters
        ----------
        h5file : PyTables File
            the hdf5 file
        prefix : string
            the absolute path to the group for tables of this species

        Returns
        -------
        groups : list of cyclopts_io.Groups
            All groups that could be written to by this species.
        """
        return []

    def register_tables(self, h5file, prefix):
        """Derived classes can implement this function and return their list of
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
        return []

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

    def record_point(self, point, param_uuid, io_manager=None):
        """Derived classes must implement this function, recording information
        about a parameter point in the appropriate tables.
        
        Parameters
        ----------
        point : tuple or other
            A representation of a point in parameter space
        param_uuid : uuid
            The uuid of the point in parameter space
        io_manager : cyclopts_io.IOManager, optional
            IOManager that gives access to tables/groups for writing
        """
        raise NotImplementedError

    def gen_inst(self, point, instid=None, io_manager=None):
        """Derived classes must implement this function, returning a
        representation of a problem instance.
        
        Parameters
        ----------
        point : tuple or other
            A representation of a point in parameter space
        instid : uuid
            the id for the instance, optional
        io_manager : cyclopts_io.IOManager, optional
            IOManager that gives access to tables/groups for writing
        
        Returns
        -------
        inst : tuple or other
            A representation of a problem instance to be used by this species' 
            family
        """
        raise NotImplementedError
    
    def post_process(self, instid, solnids, props, tbls):
        """Derived classes can implement this function to output interesting
        aggregate data during a post-processing step after some number of
        instance executions.
        
        Parameters
        ----------
        instid : UUID 
            UUID of the instance to post process
        solnids : tuple of UUIDs
            a collection of solution UUIDs corresponding the instid 
        props : tuple, other, possibly None
            as defined by the return value of the species' family
        tbls : 3-tuple of cyclopts.cyclopts_io.Tables
            tables from an input file, tables from an output file,
            and tables from a post-processed file
        """
        pass
