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

A problem family class must implement the following methods:

* ``register_tables``
* ``record_inst`` 
* ``read_inst``
* ``run_inst``
* ``record_soln``
* ``name``
* ``property_table_name``

Implementing a New Problem Species
----------------------------------

A problem species class must implement the following functions:

* ``register_tables``
* ``read_space``
* ``record_point``
* ``points``
* ``n_points``
* ``gen_inst``
* ``family``
* ``name``

Workflow
--------

After implementing a custom problem family and species, the Cyclopts workflow is
as follows.

* Write a parameter space run control file

* ``cyclopts convert`` the space into instances

* either 

  * ``cyclopts exec`` the instances locally or 

  * ``cyclopts condor-submit`` them, wait for their completion, and 
    ``cyclopts condor-collect`` the results

* ``cyclopts combine`` the input and output databases

* analyze the results

Tips
----

Having to declare the family/species module and class names on the command line
or in every run control file can be rather annoying. You can set global run
control parameters by adding a ``~/.cyclopts.rc`` file to your system. If no
other class or module entries are found in either the CLI or declared run
control file, this location is searched.