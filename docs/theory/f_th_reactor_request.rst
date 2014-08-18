:tocdepth: 2

Fast/Thermal Reactor Request-Based Exchange
============================================

The primary criticism agaisnt a random assignment of commodities, preference
coefficients, and constraint coefficients is that using domain-specific models
provides specific structure to a given formulation. This problem species is
designed to target a specific set of cases that focus randomness in the
domain-related values and defines domain-specific translations from those values
to the associated coefficients.

Model Fidelity
--------------

Furthermore, this species is specifically targeted at investigating the effects
of model fidelity on a given formulation. Eight different fidelity "levels" have
been defined in three categories.

===================  =====================================
Category             Subcategory
===================  =====================================
Facility Models      - Reactor Requests (batch/assem)

                     - Supply Constraints (inv/inv + process)
-------------------  -------------------------------------
Fuel Cycle           - Once-Through

                     - UOX + MOX F/Th Recycle

                     - UOX + MOX F/Th Recycle + Thorium F Recycle
-------------------  -------------------------------------
Geospatial           - None

                     - Coarse
		     
                     - Fine
===================  =====================================

Commodities
-----------

There are four possible commodities based on the fuel cycle fidelity modeled:

* enriched UOX
* fast MOX
* thermal MOX
* fast ThOX

Facility Models
---------------

Reactors
++++++++

request enrichment and commod_{i, j}

enr per request

recycled fraction for thermal reactors

Supporting Facilities
+++++++++++++++++++++

conversion functions, rhs equation

Fuel Cycles
-----------

which facilties and commodies exist where

Geospatial Assignment
---------------------

Geospatial values can be assigned in either a coarse or fine fashion. In both
cases, a location proxy is assigned uniformly, e.g., on :math:`[0, 10]`. If
coarse, then the locations are binned, representing regional or institutional
proxies.

Once geospatial values are assigned, they can then affect preferences. A
surrogate model function is required, and one suggestion is 

.. math::

   p_{loc}(i, j) = \exp(- \| loc_{i} - loc_{j} \| )

Where :math:`loc_i` is either a bin number or continuous location proxy.

Parameters
++++++++++

    n_bins : the number of bins if coarse

Surrogate Models
++++++++++++++++

    :math:`p_{loc}(i, j)` : locational based preference

Preference Determination
------------------------

qual-to-prox ratio, preference function