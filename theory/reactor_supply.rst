Overview
========

This section describes the resource exchange generation for the case where
reactors are supplying used fuel to supporting facilities. The primary goal is
to discern what are the possible options that parameterize a given instance of
such an exchange in order to test the underlying formulation under different
scalings of these parameters.

A supply group corresponds to a supply of reactor used fuel item which represent
assembly-like objects. In general, supply groups will be generated in much the
same way that demand groups are generated in the reactor request case, except
that the the number and commodity of their supply nodes is known at solution
time. Supply constraints are also simpler. Each unit coefficient is unity and
the supply value is set to the assembly mass, however their total number is much
larger, as there is one per assembly.

A request group corresponds to a supporting facility's request for used reactor
fuel. Accordingly, a request group may be comprised of multiple commodity
demands (e.g., fast/thermal reactor fuels A and B), where each commodity is
represented by a node. Demand constraints will mirror the supply constraints of
the reactor request exchange in that the demand constraint values are not
necessarily related (e.g. process versus inventory constraints).

Parameters
==========

number of commodities
---------------------

The number of commodities associated with the exchange.

Distribution Candidacy
~~~~~~~~~~~~~~~~~~~~~~

None

Theoretical Basis
~~~~~~~~~~~~~~~~~

The number of commodities is a fundamental parameter for resource exchange.

number of suppliers
-------------------

The number of reactors being modeled.

Distribution Candidacy
~~~~~~~~~~~~~~~~~~~~~~

None

Theoretical Basis
~~~~~~~~~~~~~~~~~

The number of suppliers is a fundamental parameter for resource exchange.

assemblies per supplier
-----------------------

How many items to model a supplier providing. Nominally, a small number (1, 2)
corresponds to a "batch"-type fueling system whereas a large number corresponds
to an assembly-type fueling system. Each assembly corresponds to a node in the
exchange graph. .

It is likely that this parameter will be sampled bimodally -- in small numbers
(i.e., 1 - 3) to model batch-type reactors and in large numbers (40 - 65). The
large number scaling is indicative of a range for an AP1000 operating in a
4-batch mode (i.e., 157 / 4) to a "Typical XL Plant" running in 3-batch mode
(i.e., 193 / 3) (see
http://www.nrc.gov/reactors/new-reactors/design-cert/ap1000/dcd/Tier%202/Chapter%204/4-1_r14.pdf).

Distribution Candidacy
~~~~~~~~~~~~~~~~~~~~~~

Possibly a integral distribution around an average.   

Theoretical Basis
~~~~~~~~~~~~~~~~~

The number of assemblies per supplier is directly proportional to the total
number of supply nodes. Therefore, scaling all supply simultaneous simply
results in a larger problem size. Medium-scale problem sizes are handled by
medium-scale number of assemblies.

commodities per supplier
------------------------

The number of commodities in a supplier's assembly group.

Distribution Candidacy
~~~~~~~~~~~~~~~~~~~~~~

A reasonable range is [1, 4]. Two distributions are required to assign
commodities to suppliers:

* the number of commodities
* the commodities themselves

Initial attempts for the number of commodities will use an integral value future
attempts may use an integral distribuition centered on that value. Initial
attempts for commodity selection will include a flat distribution and future
attempts may include preferential distributions (e.g., for cases where UOX, MOX,
and ThOX are possible commodities, but UOX and MOX have a higher usage
probability than ThOX).

Theoretical Basis
~~~~~~~~~~~~~~~~~

Reactors may expel more than one commodity type given their input commodity
types, and simulations will determine the variation and distribution of these
commodity types.

assembly commodity
------------------

Given that a supplier has a number of assemblies and a number of commodities,
assemblies must be assigned commodities.

Distribution Candidacy
~~~~~~~~~~~~~~~~~~~~~~

Two primary distributions are considered, given the number and type of
commodities of which a reactor's assembly group is comprised. The first is a
flat distribution, i.e., assemblies have an equal probability of being assigned
any commodity in the pool. The second is a preferred distribution (e.g.,
decaying exponential), which models a situation in which reactors have a
preference over their commodity types and have achieved their preference to some
degree of satisfaction.

Theoretical Basis
~~~~~~~~~~~~~~~~~

Simulations mechanics will determine the actual distribution of assembly
commodities for an arbitrary reactor, however, the above distributions model two
distinct use cases: cases in which reactors have no preference over their
commodity type and the case in which they do.

exclusion probability
---------------------

The probability that a given supply will be exclusive (i.e., models a quantized
assembly).

Distribution Candidacy
~~~~~~~~~~~~~~~~~~~~~~

Possibly a distribution around an average, but unlikely. 

Theoretical Basis
~~~~~~~~~~~~~~~~~

This parameter is directly related to the assembly modeling fidelity required by
a given reactor model. A value of 0 implies minimum fidelity, a value of 1
implies maximum fidelity, and it is conceiveable with module mixing that this
level of fidelity may exist on a spectrum.

number of supply constraints
----------------------------

Trivially defined as the number of assemblies.

supply constraint values
------------------------

Defined as the mass of the supplied assembly. The average mass for an assembly
is normalized to unity without loss of generality.

Distribution Candidacy
~~~~~~~~~~~~~~~~~~~~~~

Either unity for all assemblies, or a distribution as a function of commodity
and supplier around unity. The former will be analyzed first with a possible
future investigation of the latter.

Theoretical Basis
~~~~~~~~~~~~~~~~~

It is not clear how modelers will choose assembly mass size. A naive approach is
to assume all assemblies have the same size. A more sophisticated, and much more
complicated, approach assumes that size is a function of reactor type (i.e.,
supplier) and commodity type.


number of requesters
--------------------

The number of requesters. A requester may request more than one commodity. By
definition, there must be at least one requester per commodity. If there are
more requesters than commodities, the additional requesters are randomly
assigned base commodities.

Distribution Candidacy
~~~~~~~~~~~~~~~~~~~~~~

None

Theoretical Basis
~~~~~~~~~~~~~~~~~

The number of requesters is a fundamental parameter for resource exchange.

fraction of multicommodity requesters
-------------------------------------

The fraction of requesters that request more than one commodity. 

Distribution Candidacy
~~~~~~~~~~~~~~~~~~~~~~

Possibly a distribution around an average.

Theoretical Basis
~~~~~~~~~~~~~~~~~

An example might include a fast reactor fuel requester that requests multiple
types of fast reactor fuel defined as different commodities.

number of commodities per requester
-----------------------------------

The average number of commodities that a multicommodity requester supplies. 

Distribution Candidacy
~~~~~~~~~~~~~~~~~~~~~~

Primarily two cases of interest exist. The first assumes a relatively even
distribution of requesters per commodity. The second assumes that the
distribution peaks at some commodity, while some are minimally satisfied. The
former case will be investigated first.

Theoretical Basis
~~~~~~~~~~~~~~~~~

A used fuel requester may request more than one commodity, e.g., a fast reactor
fuel requester may offer two types of fast reactor fuel which are istopically
similar but treated as separate commodities.

number of request constraints
-----------------------------

A requester may have an arbitrary number of request constraints that may or may
not be related. A estimated reasonable range to model is [1, 4].

Distribution Candidacy
~~~~~~~~~~~~~~~~~~~~~~

Requesters can either all be modeled as having the same number of constraints or
a distribution can be sampled around an average. In effect, both sample a
spectrum of total requester constraints, where the former represents a few
special cases of the latter, where the distribution is uniformly sampled around
integral values.

Theoretical Basis
~~~~~~~~~~~~~~~~~

A requester may have more than one constraint on their request.

request constraint values
-------------------------

As previously mentioned, request constraints need not be related. Classic
examples provided so far are inventory constraints (i.e., a requester may have
only so much room for new resources) and a processing constraint (i.e., it will
only take as much as it can process, which may be an arbitrary function of
resource quality).

An identical approach to the reactor request supply constraints and values will
be taken.

Distribution Candidacy
~~~~~~~~~~~~~~~~~~~~~~

See reactor request supply constraints and values.

Theoretical Basis
~~~~~~~~~~~~~~~~~

See reactor request supply constraints and values.

unit capacity/demand coefficient values
---------------------------------------

An identical approach to the reactor request case will be taken.

preference coefficient values
-----------------------------

An identical approach to the reactor request case will be taken.

connection probability
----------------------

An identical approach to the reactor request case will be taken.
