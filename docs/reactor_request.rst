
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
commodities are assigned randomly.

number of supply constraints
----------------------------

The average number of additional supply constraints that a supply group adds to
the solver.

number of demand constraints
----------------------------

The average number of additional demand constraints that a supply group adds to
the solver.

supply constraint values
------------------------

demand constraint values
------------------------

unit capacity coefficient values
--------------------------------

preference coefficient values
-----------------------------
