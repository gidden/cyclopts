:tocdepth: 2

Fast/Thermal Reactor Request-Based Exchange
============================================

The primary criticism agaisnt a random assignment of commodities, preference
coefficients, and constraint coefficients is that using domain-specific models
provides specific structure to a given formulation. This problem species is
designed to target a specific set of cases that focus randomness in the
domain-related values and defines domain-specific translations from those values
to the associated coefficients.

The goal of this document is to provide a basis for the values used in modeling
the request-based exchange and to explore the effects of increasing various
kinds of fidelity on the general performance of the formulation.

Model Fidelity
--------------

Furthermore, this species is specifically targeted at investigating the effects
of model fidelity on a given formulation. Eight different fidelity "levels" have
been defined in three categories.

.. fidelity-start

===================  =====================================
Category             Subcategory
===================  =====================================
Reactor              - batch

                     - assembly
-------------------  -------------------------------------
Fuel Cycle           - Once-Through

                     - UOX + MOX F/Th Recycle

                     - UOX + MOX F/Th Recycle + Thorium F Recycle
-------------------  -------------------------------------
Location             - None

                     - Coarse
		     
                     - Fine
===================  =====================================

.. fidelity-end

Commodities
-----------

There are four possible commodities based on the fuel cycle fidelity modeled:

* enriched UOX
* fast MOX
* thermal MOX
* fast ThOX

Facilities
---------------

In order to allow for rapid instance generation, surrogate models of facilties
must be used. Surrogate models simplify the decision making that would normally
occur in agent archetypes. The goal of using surrogate models is provide
instances generally domain-valid structure.

Material
++++++++

All surrogate facility models require a notion of materials. Because simplicity
is required, materials have two properties: a commodity and fissile
enrichment. Certain commodities are fungible, e.g., fast and thermal
plutonium. Fungible commodities are delineated by preference assignment and
supplier process coefficients, both of which described in the following
sections.

Reactors
++++++++

Two types of reactors are used: thermal and fast. Thermal reactors are
simplified models of `AP-1000 <https://aris.iaea.org/sites/core.html>`_
reactors, and fast reactors are simplified models of `BN-600
<http://www-pub.iaea.org/books/IAEABooks/7609/Liquid-Metal-Cooled-Reactors-Experience-in-Design-and-Operation>`_
reactors.

Using the dimensions in the following table, one can estimate that the AP-1000
core volume is approximately 12.5 times larger than the BN-600 core. The
remainder of this section will assume BN-600 reactor cores have size unity and
AP-1000 cores have size 12.5, respectively, and that fuel density is
approximately equivalent.

.. table:: Active Core Dimensions

    ======== =============== =================
    Reactor  Core Height (m) Core Diameter (m)
    ======== =============== =================
    AP1000   4.27            3.04
    BN600    0.75            2.05
    ======== =============== =================

A further simplifying assumption is that both reactor types will reload
:math:`\frac{1}{4}` of their core at any given timestep (as has been assumbed
for `other <www.tandfonline.com/doi/pdf/10.1080/18811248.2011.9711744>`_ BN-600
analyses). 

Under these assumptions, each fast reactor will request 1 unit of fuel and each
thermal reactor will request 12.5 units of fuel. Each may be further binned into
smaller quantities to more accurately model assemblies.

As a rough approximation using the figures from active core size, and assuming
that a single AP-1000 fuel assembly holds `450 kg
<http://books.google.com/books/about/Nuclear_Engineering_Handbook.html?id=EMy2OyUrqbUC>`_
of Uranium, a unit of fuel is roughly

.. math::

   \frac{450 \frac{kg}{assembly} * 157 assemblies * \frac{1}{4} core}{12.5 units} = ~1.4 \frac{tonnes}{fuel unit}

Again one fuel unit is approximately equal to a quarter of a BN-600 reactor core.

Thermal Reactors
~~~~~~~~~~~~~~~~

Thermal reactors are capable of using either UOX or recycled MOX, and have
preferences over the commodities as described below. Fissile isotope enrichments
can vary from reactor to reator and from assembly to assembly within a
reactor. Accordingly, a surrogate model of enrichment preference is used,
randomly selective an enrichment within a viable range. Furthermore, because MOX
fuel is backfilled by another istopically fertile material, it is assumed that a
MOX request is approximately `10%
<http://www.world-nuclear.org/info/Nuclear-Fuel-Cycle/Fuel-Recycling/Mixed-Oxide-Fuel-MOX/>`_
of a UOX request. The MOX enrichment range is based off `IAEA estimates
<www-pub.iaea.org/MTCD/publications/PDF/TRS415_web.pdf>`_.

.. table:: Thermal Reactor Requst Surrogate Model Summary

    ===========    =================== ==============
    Commodity      Enrichment Range    Relative Request Size
    ===========    =================== ==============
    UOX            :math:`[3.5, 5.5]`  1
    Th & F MOX     :math:`[55, 65]`    0.1
    ===========    =================== ==============

Fast Reactor
~~~~~~~~~~~~

Fast reactors come in two flavors based on the fuel cycle being modeled:
MOX-preferring reactors and ThOX-preferring reactors. Enrichment ranges are
similarly based off plutonium fissile enrichment values in the above IAEA
report. It is assumed that the Plutonium oxide in MOX takes up ~20% of the total
mass.

.. table:: Fast Reactor Requst Surrogate Model Summary

    =================    =================== ==============
    Commodity            Enrichment Range    Relative Request Size
    =================    =================== ==============
    UOX                  :math:`[15, 20]`    1 
    Th & F MOX, ThOX     :math:`[55, 65]`    0.2
    =================    =================== ==============
    
Commodity Preferences
~~~~~~~~~~~~~~~~~~~~~

.. table:: Commodity-Preference Mapping for Reactor Types

    ============  ======= ======= ======= =======
    Reactor Type  EUOX    Th MOX  F MOX   F ThOX
    ============  ======= ======= ======= =======
    Thermal       0.5     1       0.1     N/A
    F MOX         0.1     0.5     1       0.25
    F ThOX        0.1     0.25    0.5     1
    ============  ======= ======= ======= =======

Questions
~~~~~~~~~

* What critiques are there regarding the commodity-preference mapping?

  - functional form effects (e.g., linear vs. exp) could be added

* What critiques are there regarding reactory enrichment generation?

  - start simple with one enrichment per reactor, a possible upgrade is to
    introduce 2 or 3 bins around an average enrichment to emulate enrichment
    zones

Supporting Facilities
+++++++++++++++++++++

The supporting facilities represent the separations and fuel fabrications
processes for each fuel type. Supporting facilities are the suppliers in the
reactor request case, and therefore must provide supply constraints. The
supporting facility surrogate models have an inventory constraint and possibly a
process constraint, depending on the fidelity level used.

Both constraints must have an associated conversion function, that takes a
surrogate material, i.e., an enrichment and quantity.

UOX Supplier
~~~~~~~~~~~~

The UOX supplier has basic parameters, e.g., feed and tails assays, can be
safely assumed as follows

===========   =======
Parameter     Value
===========   =======
feed assay    0.711
tails assay   0.3
===========   =======

The conversion functions are also well known. 

.. math::

    conv_{inv}(\epsilon, q) = NatU(\epsilon, q)

    conv_{proc}(\epsilon, q) = SWU(\epsilon, q)

MOX and ThOX Suppliers
~~~~~~~~~~~~~~~~~~~~~~

Due to the lack of commercially viable, well documented fast reactor fuel
suppliers, a simple linear surrogate model is assumed for an inventory
constraint. There are many possible process surrogate models that could be used,
such as heat production or radiotoxicity; however, each of these requires a
detailed isotopic composition to be relevant. Per the current `IAEA practice
<http://ec.europa.eu/dgs/jrc/downloads/jrc_20100615_safeguards_heinonen.pdf>`_,
and extrapolating the same effect for reprocessing U-233, a factor,
:math:`f_{commod}`, of 100 is added for for Plutonium and Thorium-based
commodities.

.. math::

    conv_{inv}(\epsilon, q) = \epsilon q

    f_{commod} = 
    \begin{cases}
    1,& \text{if UOX}\\
    100,              & \text{otherwise}
    \end{cases}

    conv_{proc}(\epsilon, q, commod) = q f_{commod}

Supplier Constraint RHS Values
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Supporting facilities have a nominal throughput capacity. The proposed Eagle
Rock Enrichment Plant `purports
<http://us.areva.com/EN/home-203/eagle-rock-enrichment-facility.html>`_ to have
a capacity of 3.3M SWU per year, which is enough to support 25 reactors. This
work assumes a new facility could serve 25 thermal reactors requesting an
average enrichment. From previous conversations with industry representatives, a
reasonable size for a processing plant is 800 tonnes per year, which is similar
to `Rokkassho
<http://ec.europa.eu/dgs/jrc/downloads/jrc_20100615_safeguards_heinonen.pdf>`_. With
the factor of 100 discussed above, a 800 t U/ 8 t Pu facility could service
on the order of 2-3 fast reactors.

Using the following assumptions

* enrichment facilities primarily service thermal reactors
* an exchange represents a monthly timestep
* requests are based on a single unit of fuel (rather than kilograms, etc.)

.. math::

   SWU_{lwr} = SWU(\bar{\epsilon}, 12.5 * fuel unit) = ~1.1e5

   S_{proc, SWU} = \frac{25 SWU_{lwr}}{12 \frac{month}{year}} = ~2.3e5 \frac{SWU}{month} 

   S_{proc, recycle} = \frac{800 \frac{t}{year}}{12 \frac{month}{year} * 1.4 \frac{t}{fuel unit}} = ~47 \frac{fuel unit}{month} 

From the formulation point of view, interesting cases arise when either
constraint is dominated by the other and when neither is dominant. Furthermore,
instanes should be investigated in which supply is generally constrained and
when it is not. 

In order to accomplish these goals, the supply constraint values
are formulated as follows

.. math::

    S_{proc}, given

    S_{inv} = S_{proc} r_{inv, proc} \frac{conv_{proc}(\bar{\epsilon}, 1)}{conv_{inv}(\bar{\epsilon}, 1)}

Parameters
::::::::::

    :math:`r_{inv, proc}` : the ratio of the inventory RHS to the process RHS

Fuel Cycles
-----------

More commodities are required to model more complex fuel cycles. Similarly, as
more fungible commodities are added a given instance of the GFCTP becomes more
complex. This species of the GFCTP can add fuel cycle, and therefore commodity,
complexity in three steps.

Once Through
++++++++++++

The least complex fuel cycle is the Once Through (OT) fuel cycle. Reactors
request enriched uranium, and supporting facilities are represented by
Enrichment Fuel Fabricators.

Parameters
~~~~~~~~~~

None

Recycle
+++++++

Next, a Recycle (R) scenario is considered. Thermal and fast reactors are
included, and a ratio between the two is set as a parameter. Supporting
facilities include Enrichment, Thermal, and Fast Fuel Fabricators. The amount of
thermal reactors requests that can be satisfied by recycled fuel is set as a
parameter. The fraction is capped at :math:`\frac{1}{3}`, in line with current
French LWR refueling practices. In the low-fidelity reactor scenario,
:math:`f_{mox}` acts a probability that the batch request will be for thermal
mox fuel.

Parameters
~~~~~~~~~~

    :math:`r_{t, f}` : the ratio of thermal reactors to fast reactors

    :math:`f_{mox} \in [0, \frac{1}{3}]` : the fraction of thermal reactor
    requests that can be met with recycled fuel

    :math:`r_{s, r}` : the ratio of primary suppliers to their primary requesters

Recycle + Thorium
+++++++++++++++++

Finally, a fuel cycle with a thorium breeder reactor is modeled. Building on the
R scenario, the Recycle + Thorium (RTh) adds an additional fast reactor model
that prefers Thorium-based recycled fuel. The fraction of fast reactors that are
Thorium-based is set as a parameter. Additionally, a Thorium Fast Fuel
Fabricator is added to the pool of suppliers.

Parameters
~~~~~~~~~~

    :math:`r_{th, pu}` : the ratio of Thorium to Plutonium-based fast reactors

Location Assignment
---------------------

Location values can be assigned in either a coarse or fine fashion. In both
cases, a location proxy is assigned uniformly, e.g., on :math:`[0,
1]`. Locations are binned, representing regions. If coarse, only regional
relationships are taken into account; if fine, regional relationships are taken
into account as well as total proximity.

Once location values are assigned, they can then affect preferences. A
surrogate model function is required, and one suggestion is 

.. math::

   p_{l}(i, j) = \delta_{l} \frac{\exp(- | reg_{i} - reg_{j} | ) + \delta_{fine} \exp(- \| loc_{i} - loc_{j} \| )}{1 + \delta_{fine}}  

Parameters
++++++++++

    :math:`\delta_{l}` : whether to include a location preference 

    :math:`\delta_{fine}` : whether to include a fine location proxy 

    :math:`n_{reg}` : the number of regions

Surrogate Models
++++++++++++++++

    :math:`p_{l}(i, j)` : location-based preference

Preference Determination
------------------------

Given that facilities have preference assignments based on commodity matching,
:math:`p_c`, and, optionally, location, :math:`p_l`, a valid question is whether
the formulation is affected by their relative magnitude. Therefore a final
parameter is added to determine the total preference

.. math::

    p(i, j) = p_{c}(i, j) + r_{l, c} p_{l}(i, j)

Parameters
++++++++++

    :math:`r_{l, c}` : the importance ratio of location to commodity types

Parameter Summary
-----------------

All of the parameters that can be set for this species are listed below:

.. table:: Structured Request Species Parameters

    ===================== ================================================================== ==========================
    Handle                Full Name                                                          Possible Values
    ===================== ================================================================== ==========================
    :math:`f_{rxtr}`      reactor fidelity                                                   :math:`\{0, 1\}`
    :math:`f_{fc}`        fuel cycle fidelity                                                :math:`\{0, 1, 2\}`
    :math:`f_{loc}`       location fidelity                                                  :math:`\{0, 1, 2\}`
    :math:`n_{rxtr}`      number of reactors                                                 any
    :math:`r_{t, f}`      ratio of thermal reactors to fast reactors                         :math:`[0, \frac{1}{4}]`
    :math:`r_{th, pu}`    ratio of Thorium to Plutonium-based fast reactors                  :math:`[0, 1]`
    :math:`r_{s, r}`      ratio of primary suppliers to their primary requesters             :math:`[0, \frac{1}{2}]`
    :math:`f_{mox}`       fraction of thermal reactor requests that can be met with mox fuel :math:`[0, \frac{1}{3}]`
    :math:`r_{inv, proc}` ratio of the inventory RHS to the process RHS                      :math:`\{0.5, 1, 2\}`
    :math:`\delta_{l}`    whether to include a location preference                           :math:`\{0, 1\}`
    :math:`\delta_{fine}` whether to include a fine location proxy                           :math:`\{0, 1\}`
    :math:`n_{reg}`       number of regions                                                  any
    :math:`r_{l, c}`      ratio of location to commodity preference                          :math:`[0, 1]` 
    ===================== ================================================================== ==========================