Overview
========

The full exchange incorporates both the reactor requset parameters and the
reactor supply parameters and adds a notion of repositories. In general, a
repository is a back-end facility that bids on resources that could be used as
advanced reactor fuel. As such, it ties both subexchanges together, requiring
that they be solved as a larger exchange.

Parameters
==========

The full exchange requires a small number of parameters be defined in addition
to the reactor request and supply parameters. Only the number of repositories
and number of back end facilities for which a to-repository node will be added
is needed. All reactor assembly nodes are considered candidates for repository
arcs, and such arcs are chosen according to the exchange's exclusion
probability.

number of repositories
----------------------

The number of repositories associated with the exchange.

Distribution Candidacy
~~~~~~~~~~~~~~~~~~~~~~

None

Theoretical Basis
~~~~~~~~~~~~~~~~~

The number of repositories is a fundamental parameter for full resource exchange.

fraction back-end to repo
--------------------------

The fraction of back-end suppliers that can also send resources to a repository.

Distribution Candidacy
~~~~~~~~~~~~~~~~~~~~~~

Likely discrete values of 0, 0.25, 0.5, 0.75, and 1.

Theoretical Basis
~~~~~~~~~~~~~~~~~

Some suppliers may want to send their supply to repositories or reactors.

