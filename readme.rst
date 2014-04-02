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

Adding *.h/*.cc files takes a number of steps in order to hook them into the
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

