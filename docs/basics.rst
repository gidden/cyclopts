.. _basics:

=====================================================
Cyclopts Basics
=====================================================

Cyclopts is a flexible, plugin framework for defining problem instances, solving
those problem instances either locally or on a Condor-enabled High Throughput
Computing (HTC) System, and persisting the results. Cyclopts interacts with HDF5
databases. 

Nomenclature
----------------------------

Cyclopts uses the following nomenclature

Problem Family 

    A set of problems that share a similar structure. For example, Cyclus
    Exchange Graphs all have Nodes, Groups, Arcs, preferences, request and
    supply constraint quantities, and request and supply constraint
    coefficients. There is a 1-to-1 mapping between problem families and a
    collection of instance writing, instance reading, instance execution, and
    instance solution writing routines.

Problem Species

    A subset of a Problem Family that share a definition of parameter space and
    an instance generation routine that translates a point in parameter space
    into an instance of the problem with the Problem Family's structure. An
    example of a Problem Species for the Exchange Graph problem family is the
    Fast/Thermal Reactor Request species. There is a 1-to-1 mapping between
    problem species and a collection of parameter writing and
    parameter-to-instance translation routines.

Problem Instance

    A realization of a Problem Species, conforming to the structure of its
    Problem Family.

Problem Results

    A collection of results from the execution of a Problem Instance

Implementing a New Problem Family
----------------------------------

A problem family class must implement the following functions:

* ``record_instance`` 
* ``read_instance``
* ``exec_instance``
* ``record_solution``

Implementing a New Problem Species
----------------------------------

A problem species class must implement the following functions:

* ``read_space``
* ``record_point``
* ``gen_instance``


