:tocdepth: 3

.. _theory:

***************
Cyclopts Theory
***************

Cyclus is a nuclear fuel cycle simulator, and the primary consumer of fuel in
such cycles are nuclear reactors. Used fuel eventually leaves reactors and can
be stored or processed.

The mechanism by which these decisions are made in Cyclus is called a `Resource
Exchange <http://fuelcycle.org/module/dre.html>`_. Actors in the exchange can
*request* resources (e.g. fuel) and others *bid* on those requests to provide
the given resource. Actors are also allowed to place an arbitrary number of
custom constraints on collections of their requests and bids. For example, a
reactor could request two types of fuel, and constrain their requests such that
they receive only a certain quantity of fuel (i.e., any combination of fuel
types is acceptable).

Reactors are the drivers of any fuel cycle. The types and number of each type of
reactor determine the possible resource flows. A critical property of the
formulation used in the Cyclus resource exchange model is that it can be
separated into two exchanges: one in which reactors request fuel and another in
which reactors supply used fuel. This holds true in all cases *except* when

#. repositories and reactors actively compete for the same processed fuel source
   (e.g., if MOX is produced by a fuel production plant, and repositories and
   reactors both actively request that fuel)

#. if a reactor has the same input and output fuel commodity and bids on its own
   requests (i.e., it is self recycling)

In reality, neither situation occurs exactly as stated. In fuel cycle modeling
practice, both cases can be achieved by modeling them slightly differently. The
second example can be modeled as facility compound with a reactor, reprocessing
facility, and fuel fabrication facility each with a high affinity for trade with
the other. The first example can be avoided by the bidding facility delineating
between mox fuel for reactors and byproducts for storage.

Resource Exchange Generation Parameters
========================================

In order to generate random cases of resource exchanges, a parameter space must
be defined. Given a full set of selected parameters, classes of resource
exchanges that fit those parameters can be generated. The parameter space
depends on the exchange being generated:

.. toctree::
    :maxdepth: 1
   
    reactor_request
    reactor_supply
    full_xchange    

.. include:: parameter_formulation_effects.rst
    
