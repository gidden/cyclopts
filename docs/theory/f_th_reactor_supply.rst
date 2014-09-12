:tocdepth: 2

Fast/Thermal Reactor Supply-Based Exchange
============================================

The primary difference between the request and supply-based cases is that the
commodity assignment of assemblies is known, rather than being decided by the
outcome of the exchange. The supply-based exchange decides which supporting
facilities will receive used fuel.

The levels of fidelity modeled will mirror the request-based case:

.. include:: ./f_th_reactor_request.rst
    :start-after: .. fidelity-start
    :end-before: .. fidelity-end

Commodities
------------

The same commodities will be used as in the request case.

Facilities
------------

Reactors
++++++++

Reactors representing AP-1000 and BN-600-like generating units will be used to
determine used fuel supply. In order to simplify the generation of supply, each
reactor is assumed to be fueled by its preferred commodity with a randomly
chosen initial enrichment.

The primary difference between reactors of the request and supply cases is that
reactors in the supply case are offering known assembly types, whereas reactors
in the request case are requesting an array of assembly types. Accordingly, the
assembly types in the supply case must be chosen. If the instance is of high
reactor fidelity, the assembly types will be assigned according to the reactor's
distribution parameter. If the instance is of low reactor fidelity, the
distribution parameters serve as commodity assignment probabilities for the
reactor's entire batch.

Parameters
~~~~~~~~~~

Reactor parameters will include all those of the request instance plus

    :math:`d_{th}` : the distribution of thermal reactor assembly commodities

    :math:`d_{f_{mox}}` : the distribution of fast mox reactor assembly commodities

    :math:`d_{f_{thox}}` : the distribution of fast thox reactor assembly commodities

Supporting Facilities
+++++++++++++++++++++

The same supporting facilities will be used with the addition of a Repository
and the subtraction of the Enrichment Facility.

Parameters
~~~~~~~~~~

Supporing facility parameters will include all those of the request instance plus

    :math:`r_{repo}` : the ratio of repositories to other supporting
    facilities

Commodity Preferences
~~~~~~~~~~~~~~~~~~~~~

Preferences are assigned to facility types based on the fuels they would prefer
to process. It is assumed that facilities would prefer to process undesireable
fuels over shutting down. Further, it is assumed that any processing facility
can process used UOX. Finally, it is assumed that there is a incentive for
material to be sent to processing facilities over repositories.

.. table:: Commodity-Preference Mapping for Supporting Facility Types

    ==================  ======= ======= ======= =======
    Facility Type       EUOX    Th MOX  F MOX   F ThOX
    ==================  ======= ======= ======= =======
    Thermal Recycle     1       1       0.5     N/A
    Fast MOX Recycle    0.5     0.5     1       N/A
    Fast ThOX Recycle   0.3     N/A     N/A     1
    Repository          0.01    0.01    0.01    0.01
    ==================  ======= ======= ======= =======

Constraints
~~~~~~~~~~~

In addition to a raw throughput capacity constraint of 800 t/yr of material,
recycle facilities requesting material will be supply a fissile content demand
constraint with the coefficient and RHS are shown below, where
:math:`\bar{\epsilon} r_{commod}` is determined by the mean quantity of fissile
materail of the primary supplier to given requester.

.. math::

    conv_{fiss}(\epsilon, q) = \epsilon r_{commod} q

    S_{fiss} = \bar{\epsilon} r_{commod} \frac{800 \frac{t}{year}}{12 \frac{month}{year}} = ~66.7 \bar{\epsilon} r_{commod} \frac{t}{month} 


Repostories will employ a simple, quantity-based supply constraint. To determine
an appropriate RHS, I assume a Yucca Mountain statutory limit of 17,000 tonnes
and a 30 year lifetime, resulting in ~575 t per year processing capacity. In
fuel units, the RHS value becomes

.. math::

    S_{proc} = \frac{575 \frac{t}{year}}{12 \frac{month}{year}} = ~48 \frac{t}{month}

Fuel Cycles
-----------

The same fuel cycles will be modeled as in the request case.

Location Assignment
---------------------

Location considerations will be handled in the same manner as the request
case.

Preference Determination
------------------------

Preferences will be determined in the same manner as the request case.

Parameter Summary
-----------------

In addition to all :ref:`Request Parameters <request_params>`, the following
parameters can be set in a run control file for the supply case:

.. table:: Structured Supply Species Parameters

    ======================= ================================================================== =================================================================================
    Handle                  Full Name                                                          Possible Values
    ======================= ================================================================== =================================================================================
    :math:`d_{th}`          thermal reactor assembly distribution                              :math:`[x_{uox}, x_{{mox}_{th}}, x_{{mox}_{f}}], x_i \in [0, 1)`
    :math:`d_{f_{mox}}`     fast mox reactor assembly distribution                             :math:`[x_{uox}, x_{{mox}_{th}}, x_{{mox}_{f}}, x_{{thox}_{f}}], x_i \in [0, 1)`
    :math:`d_{f_{thox}}`    fast thox reactor assembly distribution                            :math:`[x_{uox}, x_{{mox}_{th}}, x_{{mox}_{f}}, x_{{thox}_{f}}], x_i \in [0, 1)`
    :math:`r_{repo}`        repository to supporting facility ratio                            :math:`[0, 2]`
    ======================= ================================================================== =================================================================================
    