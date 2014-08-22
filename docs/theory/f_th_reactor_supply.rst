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

Parameters
~~~~~~~~~~

    :math:`f_{t, f}` : the ratio of thermal reactors to fast reactors

    :math:`f_{mox} \in [0, \frac{1}{3}]` : the fraction of thermal reactor
    used fuel that is MOX

    :math:`f_{th, pu}` : the ratio of Thorium to Plutonium-based fast reactors

Supporting Facilities
+++++++++++++++++++++

Four types of supportin facilities will be modeled: 

* Thermal Recycle
* Fast MOX Recycle
* Fast ThOX Recycle
* Repository

Constraints
~~~~~~~~~~~

Recycle facilities will maintain the same constraint coefficients and RHS values
as the reactor request, except they are interpreted as demand
constraints. 

Repostories will employ a simple linear combination quantity processing
constraint based on the total fuel exiting a reactor via its relative quantity
measure.

.. math::

    conv_{proc}(\epsilon, q) = \frac{q}{r_{rxtr, commod}}

To determine an appropriate RHS, I assume a Yucca Mountain statutory limit of
17,000 tonnes and a 30 year lifetime, resulting in ~575 t per year processing
capacity. In fuel units, the RHS value becomes 

.. math::

    S_{proc} = \frac{575 \frac{t}{year}}{12 \frac{month}{year} * 1.4 \frac{t}{fuel unit}} = ~35 \frac{fuel unit}{month}

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
    Fast ThOX Recycle   0.5     N/A     N/A     1
    Repository          0.1     0.1     0.1     0.1
    ==================  ======= ======= ======= =======

Parameters
~~~~~~~~~~

    :math:`f_{repository}` : the ratio of repositories to other supporting
    facilities

    :math:`f_{t, f}` : the ratio of thermal recycle facilities to fast recycle
    facilities

    :math:`f_{mox, th}` : the ratio of MOX fast recycle facilities to ThOX fast
    recycle facilities

Location Assignment
---------------------

Location considerations will be handled in the same manner as the request
case.