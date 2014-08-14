
####################################################
Cyclopts: Optimization Analysis Framework for Cyclus
####################################################

Cyclopts is an `HTCondor-aware <http://research.cs.wisc.edu/htcondor/>`_
platform designed to enable large-scale parameter space exploration of
computational problems. It's primary use is to analyze supported optimization
problems found in the `Cyclus <http://fuelcycle.org/>`_ nuclear fuel cycle
simulator. Because Cyclus only defines a C++ API, `Cython <http://cython.org/>`_
wrappings are automatically generated via `XDress <http://xdress.org/>`_.

.. warning::

  Cyclopts is currently under heavy development and purely experimental! With
  great power comes great responsibility!

********
Overview
********

Cyclopts is a framework that is designed to test and analyze computational
problems, with optimization problems being a primary use case. Cyclopts provides

* a canonical way to describe the possible parameter space that define such
  problems

* a canonical representation of problem instances

* the ability to execute problem instances that meet given conditions with a
  variety of solvers

* the ability to perform these executions using the `High Throughput Computing
  <http://en.wikipedia.org/wiki/High-throughput_computing>`_ (HTC) platform
  `HTCondor <http://research.cs.wisc.edu/htcondor/>`_

* a utility to view and compare results

********
Contents
********

.. toctree::
    :maxdepth: 1
    
    install
    basics
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

