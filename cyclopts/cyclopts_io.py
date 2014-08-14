"""This module provides I/O classes and routines for Cyclopts-related functionality.

:author: Matthew Gidden <matthew.gidden _at_ gmail.com>
"""
import numpy as np
import tables as t
import math
import datetime

import cyclopts
import cyclopts.tools as tools
        
class Table(object):
    """A thin wrapper for a PyTables Table to be used by Cyclopts.
    """

    def __init__(self, h5file, path, dt=None, chunksize=None):
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
        """
        self.h5file = h5file
        self.path = path
        self.dt = dt
        # l1 cache size / row size / 2
        # factor of 2 is ideal for reading/writing speed (per @scopatz's advice)
        chunksize = chunksize if chunksize is not None \
            else math.floor(32 * 1024 / float(dt.itemsize) / 2)
        self.chunksize = int(chunksize)
        self.prefix = '/'.join(self.path.split('/')[:-1])
        if not self.prefix.startswith('/'):
            self.prefix = '/{0}'.format(self.prefix)
        self.name = self.path.split('/')[-1]
        self._data = np.empty(shape=(self.chunksize), dtype=self.dt)
        self._idx = 0
        self._tbl = self.h5file.get_node(self.path) if self.path in self.h5file \
            else None

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

    def instid_rows(self, uuid):
        return self._tbl.where('instid == uuid')

    def append_data(self, data):
        """Appends data to the Table. If the chunksize limit is reached, data is
        written to disc.

        Parameters
        ----------
        data : np.ndarray
            data to append to the table
        """
        ndata = len(data)
        idx = self._idx
        chunksize = self.chunksize
        # just add data, no writing
        if ndata + idx < chunksize:
            self._idx += ndata
            self._data[idx:self._idx] = data
            return

        # writing
        space = chunksize - idx
        nwrites = 1 + int(math.floor(float(ndata - space) / chunksize))
        self._data[idx:chunksize] = data[:space]
        self._idx = chunksize
        self._write()
        for i in range(nwrites - 1):
            start = i * chunksize + space
            stop = (i + 1) * chunksize + space
            self._write(data[start:stop])
        self._idx = ndata - (nwrites - 1) * chunksize - space
        if self._idx > 0:
            self._data[:self._idx] = data[-self._idx:]
            
    def flush(self):
        """Writes any remaining data to the table. This must be called before
        closing the h5file."""
        self._write()

    def _write(self, data=None):
        """Writes data up to self.idx"""
        if self._tbl is None:
            raise IOError('Table must be created before it can be written to.')
        if data is None:
            self._tbl.append(self._data[:self._idx])
            self._idx = 0
        else:
            self._tbl.append(data)
        self._tbl.flush()        

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
            if tbl.path not in self.h5file:
                tbl.create()

    def __del__(self):
        if self.h5file.isopen:
            self.flush_tables()
    
    def flush_tables(self):
        for tbl in self.tables.values():
            tbl.flush()
