#!/usr/bin/env python
from __future__ import print_function
 
import os
import sys
import subprocess

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

# much of the inspiration for this setup file has come from pyne (pyne.io)

# Thanks to http://patorjk.com/software/taag/
cyclopts_logo = r""" 
   ___           _             _       
  / __\   _  ___| | ___  _ __ | |_ ___ 
 / / | | | |/ __| |/ _ \| '_ \| __/ __|
/ /__| |_| | (__| | (_) | |_) | |_\__ \
\____/\__, |\___|_|\___/| .__/ \__|___/
      |___/             |_|            
"""

INFO = {
    'version': '0.0.6',
    }

def parse_args():
    distutils_args = []
    cmake = []
    make = []
    argsets = [distutils_args, cmake, make]
    i = 0
    for arg in sys.argv:
        if arg == '--':
            i += 1
        else:
            argsets[i].append(arg)
    hdf5opt = [o.split('=')[1] for o in distutils_args if o.startswith('--hdf5=')]
    if 0 < len(hdf5opt):
        os.environ['HDF5_ROOT'] = hdf5opt[0]  # Expose to CMake
        distutils_args = [o for o in distutils_args if not o.startswith('--hdf5=')]
    # Change egg-base entry to absolute path so it behaves as expected
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--egg-base')
    res, distutils_args = parser.parse_known_args(distutils_args)
    if res.egg_base is not None:
        local_path = os.path.dirname(os.path.abspath(sys.argv[0]))
        distutils_args.append('--egg-base='+os.path.join(local_path, res.egg_base))
    return distutils_args, cmake, make

def cyclopts_setup():
    
    scripts_dir = \
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scripts')
    scripts = [os.path.join(scripts_dir, f)
               for f in os.listdir(scripts_dir)]

    packages = [
        'cyclopts', 
        'cyclopts.condor',
        'cyclopts.structured_species',
        ]
    pack_dir = {
        'cyclopts': 'cyclopts',
        'cyclopts.condor': 'cyclopts/condor',
        'cyclopts.structured_species': 'cyclopts/structured_species',
        }
    extpttn = ['*.dll', '*.so', '*.dylib', '*.pyd', '*.pyo']
    pack_data = {
        'cyclopts': ['*.pxd', 'include/*.h', 'include/*.pxi',] + extpttn,
        'cyclopts.condor': extpttn,
        'cyclopts.structured_species': extpttn,
        }
    setup_kwargs = {
        "name": "cyclopts",
        "version": INFO['version'],
        "description": 'The Cyclus Optimization Analysis Package',
        "author": 'Matthew Gidden',
        "author_email": 'matthew.gidden@gmail.com',
        "url": 'http://github.com/gidden/cyclopts',
        "packages": packages,
        "package_dir": pack_dir,
        "package_data": pack_data,
        "scripts": scripts,
        "zip_safe": False,
        }
    rtn = setup(**setup_kwargs)

def final_message(success=True):
    if success:
        return

    msg = "\n\nUSAGE: "
    "python setup.py <distutils-args> [-- <cmake-arg>] [-- <make-args>]\n"
    "CMake and make command line arguments are optional, but must be preceeded "
    "by '--'.\n"
    
    print(msg)

def main_body():
    if not os.path.exists('build'):
        os.mkdir('build')
    sys.argv, cmake_args, make_args = parse_args()
    makefile = os.path.join('build', 'Makefile')
    if not os.path.exists(makefile):
        rtn = subprocess.call(['which', 'cmake'])
        if rtn != 0:
            sys.exit('CMake is not installed, aborting Cyclopts build.')
        cmake_cmd = ['cmake', '..'] + cmake_args
        cmake_cmd += ['-DPYTHON_EXECUTABLE=' + sys.executable, ]
        rtn = subprocess.check_call(cmake_cmd, cwd='build', 
                                    shell=(os.name=='nt'))
    rtn = subprocess.check_call(['make'] + make_args, cwd='build')
    cwd = os.getcwd()
    os.chdir('build')
    cyclopts_setup()
    os.chdir(cwd)

def main():
    success = False
    print(cyclopts_logo)
    try:
        main_body()
        success = True
    finally:
        final_message(success)

if __name__ == "__main__":
    main()

