:tocdepth: 2

Random Reactor Request-Based Exchange
======================================

This section describes the resource exchange generation for the case where
reactors are ordering fuel from suppliers. The primary goal is to discern what
are the possible options that parameterize a given instance of such an exchange
in order to test the underlying formulation under different scalings of these
parameters.

A request group represents a reactor fuel request where items (nodes) in that
request satisfy the same demand. For example, a fast reactor may make a request
for assemblies for its radial blanket. Such a request could include mostly
natural uranium, but a subset may be replaceable with thorium. 

A variety of parameters are required to described an instance of a resource
exchange where reactors request fuel. The sum of these parameters define the
state of the exchange, which is comprised of both supply and request groups and
individual nodes within those groups. A parameter either represents a constant
value for each group it parameterizes or it represents an average value,
distribution, and related information, and the group-specific value is sampled
for each run of that ^instance^ of the exchange. As may be expected, average
values are used in cases where it does not make sense for the system state in
question to be modeled as constant across the entire system. For example, since
request nodes roughly model the number of assemblies being ordered by a reactor,
it makes more sense for this to be an average value rather than a static
value. By using an average value, the model provides insight into cases where
most reactors order ^around^ that many assemblies. In general, constant values
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

Distribution Candidacy
^^^^^^^^^^^^^^^^^^^^^^

None

Theoretical Basis
^^^^^^^^^^^^^^^^^

The number of commodities is a fundamental parameter for resource exchange.

number of requesters
--------------------

The number of request groups, where a group defines an overall request that will
fuel a reactor. Some portion of that request may be satisfied by more than one
commodity.

Distribution Candidacy
^^^^^^^^^^^^^^^^^^^^^^

None

Theoretical Basis
^^^^^^^^^^^^^^^^^

The number of requesters is a fundamental parameter for resource exchange.

assemblies per request
----------------------

How many items to include in the request group. Nominally, a small number (1, 2)
corresponds to a ^batch^-type fueling system whereas a large number corresponds
to an assembly-type fueling system. Generally, each assembly corresponds to a
node in the exchange graph. If an assembly can be satisfied by multiple
commodities, multiple exchange nodes will be added while the subsequent demand
constraint remains the same.

It is likely that this parameter will be sampled bimodally -- in small numbers
(i.e., 1 - 3) to model batch-type reactors and in large numbers (40 - 65). The
large number scaling is indicative of a range for an AP1000 operating in a
4-batch mode (i.e., 157 / 4) to a ^Typical XL Plant^ running in 3-batch mode
(i.e., 193 / 3) (see
http://www.nrc.gov/reactors/new-reactors/design-cert/ap1000/dcd/Tier%202/Chapter%204/4-1_r14.pdf).

Distribution Candidacy
^^^^^^^^^^^^^^^^^^^^^^

Possibly a integral distribution around an average.   

Theoretical Basis
^^^^^^^^^^^^^^^^^

In general, the number of assemblies per request is directly proportional to the
total number of request nodes. Therefore, scaling all requests simultaneous
simply results in a larger problem size. Medium-scale problem sizes are handled
by medium-scale number of assemblies.

total request value
-------------------

Total request values are modeling full reactor requests. A basic assumption will
be made that each assembly-type object will be equal in size and can be
represented as having a quantity of unity.

Distribution Candidacy
^^^^^^^^^^^^^^^^^^^^^^

None

Theoretical Basis
^^^^^^^^^^^^^^^^^

Perturbation effects based on variable assembly quantities manifest themselves
as variable unit coefficients on the primary request constraint. This effect is
handled by the addition of request constraints with distribution-sampled unit
coefficients.

multicommodity zone fraction
----------------------------

The fraction of requests that can be met with more than one commodity. This
expands the number of request nodes by (fraction * assemblies * (commodities - 1)).

Distribution Candidacy
^^^^^^^^^^^^^^^^^^^^^^

Possibly a (0, 1) distribution around an average. 

Theoretical Basis
^^^^^^^^^^^^^^^^^

Any non-trivial reactor-request resource exchange will involve demand that can
be met by more than one commodity. Because the total number of request nodes is
directly proportional to this parameter, a first attempt will be made with
integral values. If a distribution is used, it will simply serve as a way to
investigate problem sizes within the integral value bounds.

commodities in multicommodity zone
----------------------------------

The number of commodities that satisfy the multicommodity fraction of assemblies.

Distribution Candidacy
^^^^^^^^^^^^^^^^^^^^^^

Possibly a integral distribution around an average. 

Theoretical Basis
^^^^^^^^^^^^^^^^^

It is possible for more than one commodity to satisfy a request, and conceivable
that an arbitrary number of commodities could satisfy a request.

exclusion probability
---------------------

The probability that a given request group will be comprised of exclusive
requests. A basic assumption is made that for a given collection of requests
(i.e., request group), a reactor will want each node to either be exclusively
satisfied or not. In other words, either a request group models quantized
assemblies or it does not.

Distribution Candidacy
^^^^^^^^^^^^^^^^^^^^^^

Possibly a distribution around an average, but unlikely. 

Theoretical Basis
^^^^^^^^^^^^^^^^^

This parameter is directly related to the assembly modeling fidelity required by
a given reactor model. A value of 0 implies minimum fidelity, a value of 1
implies maximum fidelity, and it is conceiveable with module mixing that this
level of fidelity may exist on a spectrum.

number of demand constraints
----------------------------

The average number of additional demand constraints that a supply group adds to
the solver. This will follow the number of supply constraints with one
additional constraint to mirror the default mass-flow demand constraint.

Distribution Candidacy
^^^^^^^^^^^^^^^^^^^^^^

Possibly an integral distribution around an average.

If the average value is used, an integral, truncated distribution that peaks at
the average will be sampled.

Theoretical Basis
^^^^^^^^^^^^^^^^^

A given requester may have multiple filters on their requests (e.g., mass and
plutonium content).

demand constraint values
------------------------

Demand constraint values are closely related to the request values. The default
demand constraint value is equal to a given request group's total
request. Accordingly, additional demand constraint values will either be equal
to or approximately equal to the mass-flow demand constraint value, the effect
of which will be investigated.

Distribution Candidacy
^^^^^^^^^^^^^^^^^^^^^^

Possibly a distribution around the total request value for the given request
group.

Theoretical Basis
^^^^^^^^^^^^^^^^^

Two assumptions are made for additional demand constraints: that the constraint
values are proportional to the total mass of the demand (e.g. plutonium content
is proportional to the total mass for plutonium-based commodities, or reactivity
is proportional to the total mass for reactor fuel), and that variability
amongst suppliers occurs implying that unit capacities can be sampled around
unity (see below).

number of suppliers
-------------------

The number of suppliers. A supplier may supply more than one commodity. By
definition, there must be at least one supplier per commodity. If there are more
suppliers than commodities, the additional suppliers are randomly assigned base
commodities.

Distribution Candidacy
^^^^^^^^^^^^^^^^^^^^^^

None

Theoretical Basis
^^^^^^^^^^^^^^^^^

The number of suppliers is a fundamental parameter for resource exchange.

fraction of multi-commodities suppliers
---------------------------------------

The fraction of suppliers that supply more than one commodity. 

Distribution Candidacy
^^^^^^^^^^^^^^^^^^^^^^

Possibly a distribution around an average.

Theoretical Basis
^^^^^^^^^^^^^^^^^

An example might include a fast reactor fuel supplier that supplies multiple
types of fast reactor fuel defined as different commodities.

number of commodities per supplier
----------------------------------

The average number of commodities that a multicommodity supplier supplies. 

Distribution Candidacy
^^^^^^^^^^^^^^^^^^^^^^

Primarily two cases of interest exist. The first assumes a relatively even
distribution of suppliers per commodity. The second assumes that the
distribution peaks at some commodity, while some are minimally satisfied. The
former case will be investigated first.

Theoretical Basis
^^^^^^^^^^^^^^^^^

A supplier may offer more than one commodity that share constraint values, e.g.,
a fast reactor fuel supplier may offer two types of fast reactor fuel which are
istopically similar but treated as separate commodities.

number of supply constraints
----------------------------

The number of additional supply constraints that a supply group adds to
the solver. Values are integral and span [1, 3]. 

Two primary issues exist:

* what should the upper bound be (is there a good reason why it shouldn't be 3?)
* whether the number of additional constraints should be a static or average
  value

See the discussion regarding supply constraint values.

Distribution Candidacy
^^^^^^^^^^^^^^^^^^^^^^

Possibly an integral distribution around an average.

If the average value is used, an integral, truncated distribution that peaks at
the average will be sampled.

Theoretical Basis
^^^^^^^^^^^^^^^^^

A given supplier may have multiple constraints on their supply, for example
process and existing inventory constraints.

supply constraint values
------------------------

Supply constraint values drive the mass flow with respect to whether flow comes
from actual suppliers or the ^faux^ suppliers (in order to guarantee a feasible
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

Distribution Candidacy
^^^^^^^^^^^^^^^^^^^^^^

Described above.

Theoretical Basis
^^^^^^^^^^^^^^^^^

Suppliers can be constrained by more than one non-related constraint (e.g.,
process constraints and inventory constraints), which suggests the above
approach is reasonable to investigate such cases.

unit capacity/demand coefficient values
---------------------------------------

The unit capacity coefficients are designed to model the amount of capacity (or
demand) consumed by satisfying a unit of a request, i.e., if a unit of the
proposed resource flows along the arc in quesiton. 

Distribution Candidacy
^^^^^^^^^^^^^^^^^^^^^^

A distribution around unity will is used. At present a uniform distribution from
(0, 2] is used.

Theoretical Basis
^^^^^^^^^^^^^^^^^

Because the coefficients will depend on the process being modeled, e.g.,
enrichment, separations, etc., the actual translation function that produces
such coefficients can be wide ranging. Similarly, demand translation functions
can be wide ranging. However, a basic assumption is made that the relation
between the unit capacity coefficients and capacitating value is approximately
the same for demand constraints and supply constraints in the same ^class^
(i.e., full, half, quarter of required supply).

In other words, two arbitrarily chosen supply or demand constraints look
approximately the same if each is normalized.

preference coefficient values
-----------------------------

Because preferences are a relative value, a simple (0, 1) uniform distribution
is used for each preference assignment. A possible improvement would be to
sample preferences in the same neighborhood for each supplier/consumer group
pair.

Distribution Candidacy
^^^^^^^^^^^^^^^^^^^^^^

A (0, 1) uniform distribution will be used with possible clustering around
requester/supplier pairs.

Theoretical Basis
^^^^^^^^^^^^^^^^^

A simulation's entities can have an arbitrary process for providing preference
values, and a known use case includes preferring region-region or
institution-institution trades. The former implies using a simple uniform
distribution and the latter implies using a clustered distribution as described.

connection probability
----------------------

A measure of the probability that a request node and supply node of the same
commodity will be connected. A probabiliy of 0 indicates that the graph is
minimally connected (i.e., each request node has exactly one arc to it) whereas
a probability of 1 indicates that the graph is maximally connected (all possible
connections are made).

Distribution Candidacy
^^^^^^^^^^^^^^^^^^^^^^

Possibly a distribution around an average, but unlikely.  

Theoretical Basis
^^^^^^^^^^^^^^^^^

Not all possible connections are required to be accounted for, and reducing
possible connections reduces problem size.
