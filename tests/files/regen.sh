#!/bin/bash

rm test_in.h5 test_out.h5 test_pp.h5

cyclopts convert --cycrc cycloptsrc.py --db test_in.h5 --rc test.rc
cyclopts exec --cycrc cycloptsrc.py --db test_in.h5 --outdb test_out.h5 --solvers cbc
cyclopts pp  --cycrc cycloptsrc.py --indb test_in.h5 --outdb test_out.h5 --ppdb test_pp.h5