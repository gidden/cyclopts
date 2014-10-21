"""This module provides I/O classes and routines for Cyclopts-related functionality.

:author: Matthew Gidden <matthew.gidden _at_ gmail.com>
"""
import numpy as np
import tables as t
import math
import datetime
from collections import defaultdict

import cyclopts
import cyclopts.tools as tools
import cyclopts.analysis as analysis

def value_mapping(self, x, y, tbl=None, uuids=True):
    """Returns a mapping from x to a list of ys in a table. A table can be
    supplied, or the underlying table will be used by default. If uuids is
    true, the cyclopts.tools.str_to_uuid function is used for both x and
    y."""
    ret = defaultdict(list)
    if uuids:
        for row in tbl.iterrows():
            ret[tools.str_to_uuid(row[x])].append(tools.str_to_uuid(row[y]))
        else:
            for row in tbl.iterrows():
                ret[row[x]].append(row[y])
    return ret
        
class Table(object):
    """A thin wrapper for a PyTables Table to be used by Cyclopts.
    """

    def __init__(self, h5file=None, path=None, dt=None, chunksize=None, 
                 cachesize=None):
        """Parameters
        ----------
        h5file : PyTables File
            the hdf5 file
        path : string
            the absolute path to the table
        dt : np.dtype, optional
            the dtype for the table
        chunksize : int, optional
            the table chunksize, Cyclopts will optimize for a 32Kb L1 cache by
            default
        cachesize : int, optional
            the size of data to cache before writing, defaults to 100 times the 
            chunksize
        """
        self.h5file = h5file
        self.path = path if path is not None else '/'
        self.dt = dt if dt is not None else np.dtype(None) 
        # l1 cache size / row size / 2
        # factor of 2 is ideal for reading/writing speed (per @scopatz's advice)
        chunksize = chunksize if chunksize is not None \
            else math.floor(32 * 1024 / float(dt.itemsize) / 2)
        self.chunksize = int(chunksize)
        # 100 seems right, eh?
        factor = int(1e2)
        self.cachesize = factor * self.chunksize if cachesize is None else cachesize
        self.prefix = '/'.join(self.path.split('/')[:-1])
        if not self.prefix.startswith('/'):
            self.prefix = '/{0}'.format(self.prefix)
        self.name = self.path.split('/')[-1]
        self._data = np.empty(shape=(self.cachesize), dtype=self.dt)
        self._idx = 0
        self.n_writes = 0
        
        if self.h5file is not None and self.path in self.h5file:
            self._tbl = self.h5file.get_node(self.path)
        else:
            self._tbl = None

    def __del__(self):
        del self._data

    def create(self):
        """Creates a table in the h5file. This must be called before writing."""
        groups = [x for x in self.prefix.split('/') if x]
        prefix = ''
        for name in groups:
            path = '/'.join([prefix, name])
            prefix = '/' if not prefix else prefix
            if not path in self.h5file:
                self.h5file.create_group(prefix, name, title=name, 
                                         filters=tools.FILTERS)
                self.h5file.flush()
            prefix = path

        self.h5file.create_table(self.prefix, 
                                 self.name, 
                                 description=self.dt, 
                                 filters=tools.FILTERS, 
                                 chunkshape=(self.chunksize,))

        self._tbl = self.h5file.get_node(self.path)

    def table(self):
        return self._tbl

    def value_mapping(self, x, y, tbl=None, uuids=True):
        """Returns the result of value_mapping() using the underlying table."""
        return value_mapping(c, y, tbl=self._tbl, uuids=uuids)

    def rows_where(self, cond, condvars=None):
        return self._tbl.read_where(cond, condvars=condvars)
        
    def uuid_rows(self, uuid, colname='instid'):
        condvars = {'uuid': uuid.bytes}
        return self.rows_where("""{0} == uuid""".format(colname), 
                               condvars=condvars)

    def append_data(self, data):
        """Appends data to the Table. If the cachesize limit is reached, data is
        written to disc.

        Parameters
        ----------
        data : array-like
            data to append to the table
        """
        ndata = len(data)
        idx = self._idx
        arylen = self.cachesize
        # just add data, no writing
        if ndata + idx < arylen:
            self._idx += ndata
            self._data[idx:self._idx] = data
            return

        # writing
        space = arylen - idx
        n_writes = 1 + int(math.floor(float(ndata - space) / arylen))
        self._data[idx:arylen] = data[:space]
        self._idx = arylen
        self.flush()
        for i in range(n_writes - 1):
            start = i * arylen + space
            stop = (i + 1) * arylen + space
            self.flush(data[start:stop])
        self._idx = ndata - (n_writes - 1) * arylen - space
        if self._idx > 0:
            self._data[:self._idx] = data[-self._idx:]

    def writeable(self):
        return self._tbl is not None and self._tbl._v_file._iswritable()
            
    def flush(self, data=None):
        """Writes cached data to the table."""
        if not self.writeable() and data is not None and self._idx != 0:
            # not writeable but there was data to write
            raise IOError(("Cannot write data to the table {0} in unwriteable"
                           " file {1}").format(self._tbl._v_name, 
                                               self._tbl._v_file.filename))
        if not self.writeable():
            # not writeable, don't do anything
            return

        if data is None:
            self._tbl.append(self._data[:self._idx])
            self._idx = 0
        else:
            self._tbl.append(data)
        self._tbl.flush()        
        self.n_writes += 1

_result_dt = np.dtype([
                ("solnid", ('str', 16)), # 16 bytes for uuid
                ("instid", ('str', 16)), # 16 bytes for uuid
                ("solver", ('str', 30)), # 30 seems long enough, right?
                ("problem", ('str', 30)), # 30 seems long enough, right?
                ("time", np.float64),
                ("objective", np.float64),
                ("cyclopts_version", ('str', 12)),
                # len(dtime.datetime.now().isoformat(' ')) == 26
                ("timestamp", ('str', 26)), 
                ])
        
class ResultTable(Table):
    """A Cyclopts Table for generic results.
    """

    def __init__(self, h5file, path='/Results', chunksize=None):
        """Parameters
        ----------
        h5file : PyTables File
            the hdf5 file
        path : string
            the absolute path to the table
        chunksize : int, optional
            the table chunksize, Cyclopts will optimize for a 32Kb L1 cache by
            default
        """
        super(ResultTable, self).__init__(h5file, path, _result_dt, chunksize)

    def record_soln(self, soln, soln_uuid, inst_uuid, solver):
        self.append_data([(
                    soln_uuid.bytes, 
                    inst_uuid.bytes, 
                    solver.type, 
                    soln.type, 
                    soln.time, 
                    soln.objective, 
                    cyclopts.__version__, 
                    datetime.datetime.now().isoformat(' '),
                    )])

class PathMap(analysis.PathMap):
    """A simple container class for mapping columns to Hdf5 paths
    for the Results table"""
    
    def __init__(self, col=None):
        super(PathMap, self).__init__(col)
        
    @property
    def path(self):
        return '/Results'        
        
class TableManager(object):
    """A managing class that performs RAII for its tables by creating them if
    needed upon acquisition and flushing them upon deletion. Tables can be
    accessed through the manager by its tables member, which is a dictionary
    from table names to Table objects."""

    def __init__(self, h5file, tables):
        """Parameters
        ----------
        h5file : PyTables File
            the hdf5 file
        tables : list of Tables
            the list of tables to manage
        """
        self.tables = {tbl.path.split('/')[-1]: tbl for tbl in tables}
        self.h5file = h5file
        for tbl in self.tables.values():
            if tbl.path not in self.h5file and self.h5file.mode is not 'r':
                tbl.create()

    def __del__(self):
        if self.h5file.isopen and self.h5file.mode is not 'r':
            self.flush_tables()
    
    def flush_tables(self):
        for tbl in self.tables.values():
            tbl.flush()

    def total_writes(self):
        return sum([tbl.n_writes for tbl in self.tables.values()])
