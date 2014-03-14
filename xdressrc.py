from xdress.utils import apiname
from xdress.clang.cindex import Config

import os

# parsers = "clang"

# clang_path = '/usr/lib/llvm-3.2/lib'
# if os.path.exists(os.path.join(clang_path, 'libclang.so')):
#     Config.set_library_path(clang_path)

package = 'cyclopts'     # top-level python package name
packagedir = 'cyclopts'  # location of the python package

includes = [
    os.path.expanduser('~/.local/include/cyclus'),
    '/usr/include/boost',
    ]

functions = [
    apiname('*', 'cpp/execute.*', incfiles='execute.h'),
    ]
