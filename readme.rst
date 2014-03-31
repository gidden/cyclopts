Cyclopts
========

A full, stochastic analysis of the Generic Fuel Cycle Resource Exchange formulation.

Cyclopts utilizes its Python layer to generate the run-control parameters for a
given Cyclus resource exchange. It's C++ layer makes the corresponding calls to
Cyclus to instantiate and execute the exchange. The Python-C++ communication is
made possible by using [xdress](xdress.org) to generate Cython wrappers from the
C++ source code. Pretty neat!

Adding C++ Files
================

It is nontrivial to add *.cc files to the build system, and xdress must be
informed in a number of locations.

.. code-block:: bash

    some stuff
