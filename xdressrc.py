from xdress.utils import apiname

package = 'cyclopts'     # top-level python package name
packagedir = 'cyclopts'  # location of the python package

functions = [
    apiname('run_exchange', 'cpp/distributions.*', incfiles='distributions.h'),
    ]
