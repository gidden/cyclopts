from xdress.utils import apiname

package = 'analysis'     # top-level python package name
packagedir = 'analysis'  # location of the python package

functions = [
    apiname('run_exchange', 'cpp/distributions.*', incfiles='distributions.h'),
    ]
