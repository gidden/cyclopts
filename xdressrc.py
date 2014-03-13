from xdress.utils import apiname

import os

parsers = "clang"

package = 'cyclopts'     # top-level python package name
packagedir = 'cyclopts'  # location of the python package

includes = [
    os.path.expanduser('~/.local/include/cyclus'),
    ]

functions = [
    apiname('run_rxtr_req', 'cpp/execute.*', incfiles='execute.h'),
    ]
