
Overview
========

This section describes the resource exchange generation for the case where
reactors are ordering fuel from suppliers. The primary goal is to discern what
are the possible options that parameterize a given instance of such an exchange
in order to test the underlying formulation under different scalings of these
parameters.

A request group represents a reactor fuel request where items (nodes) in that
request satisfy the same demand. For example, a fast reactor may make a request
for assemblies for its radial blanket. Such a request could include mostly
natural uranium, but a subset may be replaceable with thorium. 


Parameters
==========

A variety of parameters are required to described an instance of a resource
exchange where reactors request fuel. The sum of these parameters define the
state of the exchange, which is comprised of both supply and request groups and
individual nodes within those groups. A parameter either represents a constant
value for each group it parameterizes or it represents an average value,
distribution, and related information, and the group-specific value is sampled
for each run of that "instance" of the exchange. As may be expected, average
values are used in cases where it does not make sense for the system state in
question to be modeled as constant across the entire system. For example, since
request nodes roughly model the number of assemblies being ordered by a reactor,
it makes more sense for this to be an average value rather than a static
value. By using an average value, the model provides insight into cases where
most reactors order "around" that many assemblies. In general, constant values
are preferred, in order to reduce the overall number of runs required to achieve
representable analytics.

It should be noted that representing a resource exchange is inherently
stochastic. Take for instance a resource exchange where not every possible arc
exists (i.e., there is a supplier of a commodity that is not connected to a
consumer), the degree of which is measured by the connection probabilty
parameter. In such cases, which suppliers and consumers must be chosen
arbitrarily, an inherently random process.

number of commodities
---------------------

The number of commodities associated with the exchange.

number of requesters
--------------------

The number of request groups, where a group defines an overall request that will
fuel a reactor. Some portion of that request may be satisfied by more than one
commodity.

assemblies per request
----------------------

How many items to include in the request group. Nominally, a small number (1, 2)
corresponds to a "batch"-type fueling system whereas a large number corresponds
to an assembly-type fueling system. Generally, each assembly corresponds to a
node in the exchange graph. If an assembly can be satisfied by multiple
commodities, multiple exchange nodes will be added while the subsequent demand
constraint remains the same.

multicommodity zone fraction
----------------------------

The fraction of requests that can be met with more than one commodity. This
expands the number of request nodes by (factor * assemblies * (commodities - 1)).

commodities in multicommodity zone
----------------------------------

The number of commodities that satisfy the multicommodity fraction of assemblies.

connection probability
----------------------

A measure of the probability that an request node and supply node of the same
commodity will be connected. A probabiliy of 0 indicates that the graph is
minimally connected (i.e., each request node has exactly one arc to it) whereas
a probability of 1 indicates that the graph is maximally connected (all possible
connections are made).

exclusion probability
---------------------

The probability that a given assembly request will be exclusive (i.e., each
commodity-assembly request associated with it is exclusive).

number of suppliers
-------------------

The number of suppliers. A supplier may supply more than one commodity. By
definition, there must be at least one supplier per commodity. If there are more
suppliers than commodities, the additional suppliers are randomly assigned base
commodities.

number of commodities per supplier
----------------------------------

The average number of commodities that a supplier supplies. For each supplier,
their total number of commodities is sampled and their individual additional
commodities are assigned randomly. Accordingly, the total number of supply
groups is equal to the number of suppliers multiplied by the average number of
commodities per supplier.

number of supply constraints
----------------------------

The number of additional supply constraints that a supply group adds to
the solver. Values are integral and span [0, 3]. 

Two primary issues exist:

* what should the upper bound be (is there a good reason why it shouldn't be 3?)
* whether the number of additional constraints should be a static or average
  value

If the average value is used, an integral, truncated distribution that peaks at
the average will be sampled.

number of demand constraints
----------------------------

The average number of additional demand constraints that a supply group adds to
the solver. This will follow the number of supply constraints with one
additional constraint to mirror the default mass-flow demand constraitn.

demand constraint values
------------------------

Demand constraint values are closely related to the request values. The default
demand constraint value is equal to a given request group's total
request. Accordingly, additional demand constraint values will either be equal
to or approximately equal to the mass-flow demand constraint value, the effect
of which will be investigated.

unit capacity coefficient values
--------------------------------

The unit capacity coefficients are designed to model the amount of capacity
consumed by satisfying a unit of a request, i.e., if a unit of the proposed
resource flows along the arc in quesiton. Because the coefficients will depend
on the process being modeled, e.g., enrichment, separations, etc., the actual
translation function that produces such coefficients can be wide
ranging. However, the following assumptions are made:

* the supply constraint value is proportional to the mass flow supply constraint
* the unit capacities are distributed with an average of unity

In other words, two arbitrarily chosen supply constraints look approximately the
same if each is normalized.

The primary question remaining is which distribution to choose the unit
capacities.

supply constraint values
------------------------

Supply constraint values drive the mass flow with respect to whether flow comes
from actual suppliers or the "faux" suppliers (in order to guarantee a feasible
solution). The total amount needed to fully supply for a commodity can be known
after the demands for that commodity are formulated. Accordingly, an optimal
solution that does not involve faux suppliers can be achieved by setting the
supply constraint value for each supplier equal to that total demand.

A number of effects will be investigated for both unit capacities of unity and
random values:

* a single supply constraint per supplier set at sufficient supply
* a single supply constraint per supplier set at less-than sufficient supply
  (e.g., 1/4, 1/2, 3/4 of sufficient supply)
* multiple supply constraints, one of which is set at less than sufficient
  supply
* multiple supply constraints, more than one of which is set at less than
  sufficient supply

The goal of these experiements is to determine the effect of constrained supply
on the solution of the multicommodity formulation and the effect of more than
one constraint enforcing that effect. It is assumed that the effect of less-than
sufficient constraints will manifest with the first such constraint but will not
increase with subsequent additions.

preference coefficient values
-----------------------------

Because preferences are a relative value, a simple (0, 1) uniform distribution
is used for each preference assignment. A possible improvement would be to
sample preferences in the same neighborhood for each supplier/consumer group
pair.
