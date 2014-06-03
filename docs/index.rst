
====================================================
Cyclopts: Optimization Analysis Framework for Cyclus
====================================================

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

--------
Contents
--------

.. toctree::
    :maxdepth: 1
   
    install
    cli
    pyapi/main
   
------------
Search Links
------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

