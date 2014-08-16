Cyclopts
========

A stochastic analysis framework for supported problems, originally used to
analyze the Generic Fuel Cycle Resource Exchange formulation in `Cyclus
<http://fuelcycle.org>`_. Both local execution and remote execution via HTCondor
are supported.

Cyclopts utilizes its Python layer to generate the run-control parameters for a
given Cyclus resource exchange. It's C++ layer makes the corresponding calls to
Cyclus to instantiate and execute the exchange. The Python-C++ communication is
made possible by using `xdress <xdress.org>`_ to generate Cython wrappers from
the C++ source code. Pretty neat!

You can find the full documentation at `mattgidden.com/cyclopts
<http://mattgidden.com/cyclopts/index.html>`_.


.. _install:

Installation
============

.. install-start

Dependencies
------------

Cyclopts has the following dependencies:

   #. `CMake <http://www.cmake.org/>`_ (>= 2.8.5)
   #. `HDF5 <http://www.hdfgroup.org/HDF5/>`_
   #. `Cyclus <https://github.com/cyclus/cyclus>`_ (1.0)
   #. `Python 2.7 <http://www.python.org/>`_
   #. `NumPy <http://www.numpy.org/>`_ (>= 1.8.0)
   #. `SciPy <http://www.scipy.org/>`_
   #. `Cython <http://cython.org/>`_ (>= 0.19.1)
   #. `PyTables <http://www.pytables.org/>`_

Additionally, building the documentation requires:

   #. `Sphinx <http://sphinx-doc.org/>`_
   #. `SciSphinx <https://github.com/numfocus/scisphinx/>`_

Install Command
---------------

With its dependencies installed, Cyclopts can be installed as any other python
package.

For installing in system space:

.. code-block:: bash

  $ python setup.py install

For installing in user space:

.. code-block:: bash

  $ python setup.py install --user

.. install-end

Building the Docsumentation
---------------------------

Building the documentation is easy

.. code-block:: bash

  $ cd docs && make html

You can then view them by pointing your favorite browser at
``docs/build/html/index.html``.

Publishing Documentation
------------------------

To publish updated the docs, you must have a local copy of `gidden.github.io
<https://github.com/gidden/gidden.github.io>`_ and push rights to the repo on
github. It's likely that you don't!

If you do, however, its as easy as

.. code-block:: bash

  $ cd docs && make html && make publish

Basic Workflow Strategy
=======================

For a given exchange, all parameters and values are defined in the Python layer
using POD, STL containers, or simple structs. The C++ layer is responsible for
translating those data into a Cyclus exchange graph and solver, executing the
solve, and dumping graph and solution data to an output database using the tools
available in Cyclus. The python layer will manage which database is actually
written to (i.e., whether to write to a new database or add to an existing
one). The python layer can then manage any analysis as required on the
database(s).

Notes
=====

Implementation differences w.r.t. the Cyclus Exchange Graph
-----------------------------------------------------------

* default capacity constraint values are added at the end of the respective
  constrait coefficient and rhs value lists

Adding C++ Files
================

Adding \*.h/\*.cc files takes a number of steps in order to hook them into the
xdress workflow.

This mini-tutorial assumes that you have some header/implementation file pair,
``mycpp.h`` and ``mycpp.cc``. Of course start off by ``git add`` ing them. The
``CMakeLists.txt`` file in ``cyclopts/cpp`` will automatically add them to the build
system.

Next, update ``xdressrc.py``. If there is a class definition in ``mycpp*``, then add
a line to the ``classes`` array, e.g., ``apiname('MyClass', 'cpp/mycpp.*',
incfiles='mycpp.h')``. If there are external functions defined, then add a line
to the ``functions`` array.

Run ``xdress`` in the ``cyclopts`` project directory. A number of ``*.pxd`` and
``*.pyx`` files will be generated; ``git add`` them.

Next, inform the Python-portion of the build system that a new module should be
compiled. For the ``mycpp`` example, the following lines would be added to the end
of the ``CMakeLists.txt`` file in ``cyclopts/cyclopts``.

.. code-block:: bash

    # mycpp
    set_source_files_properties("${PROJECT_SOURCE_DIR}/cyclopts/mycpp.pyx"
                                PROPERTIES CYTHON_IS_CXX TRUE)
    cython_add_module(mycpp mycpp.pyx ${CYCLOPTS_SRC})
    target_link_libraries(mycpp dl ${LIBS})

``mycpp`` will now compile as a module of the ``cyclopts`` package when you run
``setup.py``. For example, you can grab an instance of ``MyClass``:

.. code-block:: bash

    # mycpp
    from cyclopts.mycpp import MyClass
    
    inst = MyClass()