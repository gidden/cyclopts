Overview
========

Each parameter has a theoretical basis in the real-life problem that is being
modeled and an effect on the underlying formulation. This section describes the
underlying formulation for each problem type and describes which parameters
relate to that effect.

Any given formulation is comprised of, nominally, five prime characteristics:

* the number of request nodes (unodes)
* the number of supply nodes (vnodes)
* the number of arcs
* the number of exclusive arcs
* the number of constraints

Reactor Request
---------------

Number of Request Nodes
~~~~~~~~~~~~~~~~~~~~~~~

* number of requesters
* assemblies per request
* multicommodity zone fraction
* commodities in multicommodity zone

Number of Supply Nodes
~~~~~~~~~~~~~~~~~~~~~~

* number of suppliers
* fraction of multi-commodities suppliers
* number of commodities per supplier

Number of Arcs
~~~~~~~~~~~~~~

* number of request nodes
* number of supply nodes
* connection probability

Number of Exclusive Arcs
~~~~~~~~~~~~~~~~~~~~~~~~

* exclusion probability

Number of Constraints
~~~~~~~~~~~~~~~~~~~~~

* number of supply constraints
* number of suppliers
* number of demand constraints
* number of requesters

Reactor Supply
--------------

Number of Request Nodes
~~~~~~~~~~~~~~~~~~~~~~~

* number of requesters
* fraction of multicommodity requesters
* number of commodities per requester

Number of Supply Nodes
~~~~~~~~~~~~~~~~~~~~~~

* number of suppliers
* assemblies per supplier

Number of Arcs
~~~~~~~~~~~~~~

* number of request nodes
* number of supply nodes
* connection probability

Number of Exclusive Arcs
~~~~~~~~~~~~~~~~~~~~~~~~

* exclusion probability

Number of Constraints
~~~~~~~~~~~~~~~~~~~~~

* number of assemblies
* number of requesters
* number of request constraints

Performance
-----------

Both formulation's performance will be functions of:

* number of commodities
* number of arcs
* number of exclusive arcs
* number of constraints
* unit capacity/demand coefficients
* supply constraint values
* demand constraint values
* preference coefficient values
