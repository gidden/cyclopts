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
    apiname('ProbSolution', 'cpp/problem.*', incfiles='problem.h', tarbase='_cproblem'),
    apiname('ExGroup', 'cpp/exchange_instance.*', incfiles='exchange_instance.h'),
    apiname('ExNode', 'cpp/exchange_instance.*', incfiles='exchange_instance.h'),
    apiname('ExArc', 'cpp/exchange_instance.*', incfiles='exchange_instance.h'),
    apiname('ExSolver', 'cpp/exchange_instance.*', incfiles='exchange_instance.h'),
    apiname('ExSolution', 'cpp/exchange_instance.*', incfiles='exchange_instance.h'),
    ]

functions = [
    apiname('Run', 'cpp/exchange_instance.*', incfiles='exchange_instance.h'),
    ]
