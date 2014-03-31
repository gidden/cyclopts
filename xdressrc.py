from xdress.utils import apiname
from xdress.clang.cindex import Config

import os

package = 'cyclopts'     # top-level python package name
packagedir = 'cyclopts'  # location of the python package

includes = [
    os.path.expanduser('~/.local/include/cyclus'),
    '/usr/include/boost',
    ]

classes = [
    apiname('SupplyRC', 'cpp/execute.*', incfiles='execute.h'),
    apiname('RequestRC', 'cpp/execute.*', incfiles='execute.h'),
    ]

functions = [
    apiname('*', 'cpp/execute.*', incfiles='execute.h'),
    ]
