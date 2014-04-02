from xdress.utils import apiname
from xdress.clang.cindex import Config

import os

package = 'cyclopts'     # top-level python package name
packagedir = 'cyclopts'  # location of the python package

extra_types = 'xdress_extra_types'

stlcontainers = [
    ('vector', 'float'),
    ('map', 'int', 'float'),
    ('map', 'int', 'int'),
    ('map', 'int', 'bool'),
    ('map', 'int', ('vector', 'int')),
    ('map', 'int', ('vector', 'float')),
    ('map', 'int', ('map', 'int', ('vector', 'float'))),
    ]

includes = [
    os.path.expanduser('~/.local/include/cyclus'),
    '/usr/include/boost',
    ]

classes = [
    apiname('*', 'cpp/execute.*', incfiles='execute.h'),
    ]

functions = [
    apiname('*', 'cpp/execute.*', incfiles='execute.h'),
    ]
