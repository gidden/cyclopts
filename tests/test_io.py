import numpy as np
import uuid
import os
import tables as t

import nose
from nose.tools import assert_true, assert_equal, assert_raises
from numpy.testing import assert_array_equal

from cyclopts import cyclopts_io as cycio

class TestIO:
    def setUp(self):
        self.db = ".tmp_{0}".format(uuid.uuid4())
        if os.path.exists(self.db):
            os.remove(self.db)
        self.h5file = t.open_file(self.db, mode='w',)
        self.pth = '/tbl'
        self.dt = np.dtype([('data', float)])
    
    def tearDown(self):
        self.h5file.close()
        os.remove(self.db)

    def test_create(self):
        tbl = cycio.Table(self.h5file, self.pth, self.dt, chunksize=2)
        tbl.create()
        assert_true(self.pth in self.h5file) 

    def test_throw(self):
        cyctbl = cycio.Table(self.h5file, self.pth, self.dt, chunksize=3)
        cyctbl.create()
        h5tbl = self.h5file.root.tbl
        data = np.empty(2, dtype=self.dt)
        data['data'] = range(2)
        cyctbl.append_data(data)
        assert_raises(IOError, cyctbl.flush())

    def test_write_flush(self):
        cyctbl = cycio.Table(self.h5file, self.pth, self.dt, chunksize=3)
        cyctbl.create()
        h5tbl = self.h5file.root.tbl
        data = np.empty(2, dtype=self.dt)
        data['data'] = range(2)
        cyctbl.append_data(data)
        assert_equal(0, h5tbl.nrows)
        cyctbl.flush()
        rows = self.h5file.root.tbl[:]
        assert_array_equal(data, rows)

    def test_write_single(self):
        cyctbl = cycio.Table(self.h5file, self.pth, self.dt, chunksize=3)
        cyctbl.create()
        h5tbl = self.h5file.root.tbl
        data = np.empty(4, dtype=self.dt)
        data['data'] = range(4)
        cyctbl.append_data(data)
        assert_equal(3, h5tbl.nrows)
        rows = self.h5file.root.tbl[:]
        assert_array_equal(data[:-1], rows)

    def test_write_double(self):
        cyctbl = cycio.Table(self.h5file, self.pth, self.dt, chunksize=3)
        cyctbl.create()
        h5tbl = self.h5file.root.tbl
        data = np.empty(7, dtype=self.dt)
        data['data'] = range(7)
        cyctbl.append_data(data)
        assert_equal(6, h5tbl.nrows)
        rows = self.h5file.root.tbl[:]
        assert_array_equal(data[:-1], rows)

    def test_write_triple(self):
        cyctbl = cycio.Table(self.h5file, self.pth, self.dt, chunksize=3)
        cyctbl.create()
        h5tbl = self.h5file.root.tbl

        data = np.empty(9, dtype=self.dt)
        data['data'] = range(9)
        cyctbl.append_data(data)
        assert_equal(9, h5tbl.nrows)
        rows = self.h5file.root.tbl[:]
        assert_array_equal(data, rows)

    def test_write_triple_separate(self):
        cyctbl = cycio.Table(self.h5file, self.pth, self.dt, chunksize=3)
        cyctbl.create()
        h5tbl = self.h5file.root.tbl

        data = np.empty(7, dtype=self.dt)
        data['data'] = range(7)
        cyctbl.append_data(data)
        assert_equal(6, h5tbl.nrows)
        rows = self.h5file.root.tbl[:]
        assert_array_equal(data[:-1], rows)

        data = np.empty(2, dtype=self.dt)
        data['data'] = range(2)
        cyctbl.append_data(data)
        assert_equal(9, h5tbl.nrows)
        exp = np.empty(9, dtype=self.dt)
        exp['data'] = range(7) + range(2)
        rows = self.h5file.root.tbl[:]
        assert_array_equal(exp, rows)

    def test_manager(self):
        tbls = [cycio.Table(self.h5file, self.pth, self.dt, chunksize=3)]
        manager = cycio.TableManager(self.h5file, tbls)
        h5tbl = self.h5file.root.tbl
        data = np.empty(2, dtype=self.dt)
        data['data'] = range(2)
        manager.tables['tbl'].append_data(data)
        assert_equal(0, h5tbl.nrows)
        del manager
        rows = self.h5file.root.tbl[:]
        assert_array_equal(data, rows)
