from xdress.utils import apiname
from xdress.clang.cindex import Config

import os

package = 'cyclopts'     # top-level python package name
packagedir = 'cyclopts'  # location of the python package
testdir = '.'            # location of root dir for tests, i.e., root/tests

extra_types = 'xdress_extra_types'

stlcontainers = [
    ('vector', 'int'),
    ('vector', 'float'),
    ('vector', 'ExGroup'),
    ('vector', 'ExNode'),
    ('vector', 'ExArc'),
    ('vector', ('vector', 'int')),
    ('map', 'int', 'float'),
    ('map', 'int', 'int'),
    ('map', 'int', 'bool'),
    ('map', 'int', ('vector', 'int')),
    ('map', 'int', ('vector', 'float')),
    ('map', 'int', ('vector', ('vector', 'int'))),
    ('map', 'int', ('map', 'int', ('vector', 'float'))),
    ('pair', 'int', 'int'),
     ]

includes = [
    os.path.expanduser('~/.local/include/cyclus'),
    '/usr/include/boost',
    ]

classes = [
    apiname('ExGroup', 'cpp/instance.*', incfiles='instance.h'),
    apiname('ExNode', 'cpp/instance.*', incfiles='instance.h'),
    apiname('ExArc', 'cpp/instance.*', incfiles='instance.h'),
    apiname('ExSolver', 'cpp/instance.*', incfiles='instance.h'),
    apiname('ExSolution', 'cpp/instance.*', incfiles='instance.h'),
    apiname('ProbSolution', 'cpp/instance.*', incfiles='instance.h'),
    ]
functions = [
    apiname('Run', 'cpp/instance.*', incfiles='instance.h'),
    apiname('Incr', 'cpp/instance.*', incfiles='instance.h'),
    apiname('IncrOne', 'cpp/instance.*', incfiles='instance.h'),
    ]
