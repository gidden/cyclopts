"""This module provides base classes for Problem Families, Species, and Instances.

:author: Matthew Gidden
"""
import numpy as np
import tables as t
from collections import Iterable

from cyclopts import io as cycio

class ProblemFamily(object):
    """A class representing families of problems that share the same
    structure.
    """

    def __init__(self):
        pass

    def record_inst(self):
        """Derived classes must implement this function to return a list of"""
        raise NotImplementedError

    def read_inst(self):
        """Derived classes must implement this function to return a tuple
        instance structures that can be provided to the exec_inst function.
        """
        raise NotImplementedError

    def exec_inst(self):
        """Derived classes must implement this function to take a tuple instance
        structures provided by the exec_inst function and return a ProblemResult
        or similar object.
        """
        raise NotImplementedError

class ProblemSpecies(object):
    """A class represnting species of problems that share the same parameter
    space and ProblemFamiliy."""

    def __init__(self):
        pass

    def read_space(self):
        """Derived classes must implement this function"""
        raise NotImplementedError

    def record_point(self):
        """Derived classes must implement this function"""
        raise NotImplementedError

    def gen_instance(self):
        """Derived classes must implement this function"""
        raise NotImplementedError
