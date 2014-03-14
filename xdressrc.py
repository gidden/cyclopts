from xdress.utils import apiname

import os

parsers = "clang"

package = 'cyclopts'     # top-level python package name
packagedir = 'cyclopts'  # location of the python package

includes = [
    os.path.expanduser('~/.local/include/cyclus'),
    '/usr/include/boost',
    ]

functions = [
    apiname('*', 'cpp/execute.*', incfiles='execute.h'),
    ]
