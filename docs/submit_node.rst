.. _submit_node:

Configuring a Condor Submit Node
===========================================

Cyclopts can be run on a Condor-configured system relatively easily. The
following steps are required:

* Install `Work Queue <http://ccl.cse.nd.edu/software/workqueue/>`_ on the
  submit node.

  * Update your PATH and PYTHON_PATH as suggested in the install directions.

* Run ``cyclopts cde`` on your local machine. This will send a tarred cde
  environment to the submit node to be used by Cyclopts runs.

