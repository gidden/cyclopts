
####################################################
Cyclopts: Optimization Analysis Framework for Cyclus
####################################################

Cyclopts is an `HTCondor-aware <http://research.cs.wisc.edu/htcondor/>`_
platform on which supported optimization problems found in `Cyclus
<http://fuelcycle.org/>`_ can be analyzed.

The core Cyclopts functionality provides a Python API for defining and executing
Cyclus kernel optimization problems. Because Cyclus only defines a C++ API,
`Cython <http://cython.org/>`_ wrappings are automatically generated via `XDress
<http://xdress.org/>`_.

.. warning::

  Cyclopts is currently under heavy development and purely experimental! With
  great power comes great responsibility!

********
Overview
********

Cyclopts is a framework that is designed to test and analyze optimization
problems that are a part of the `Cyclus <http://fuelcycle.org>`_ simulation
kernel. Cyclopts provides

* a canonical way to describe the possible parameter space that define such
  problems

* a canonical representation of problem instances

* the ability to execute problem instances that meet given conditions with a
  variety of solvers known to Cyclus

* the ability to perform these executions using the `High Throughput Computing
  <http://en.wikipedia.org/wiki/High-throughput_computing>`_ (HTC) platform
  `HTCondor <http://research.cs.wisc.edu/htcondor/>`_

* a utility to view and compare results


********
Contents
********

.. toctree::
    :maxdepth: 1
    
    overview   
    install
    cli
    pyapi/main
    theory/main
   
****************
Helpful Links
****************

* `Cyclus website <http://fuelcycle.org/>`_
* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

