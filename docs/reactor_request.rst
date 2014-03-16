
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

assemblies per request
----------------------

multicommodity zone fraction
-----------------------------

commodities in multicommodity zone
----------------------------------

connection probability
----------------------

exclusion probability
---------------------
