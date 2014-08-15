"""The main entry point for running Cyclopts from the command line.
"""

from __future__ import print_function

import argparse
import tables as t
import numpy as np
from collections import defaultdict
import itertools
import uuid
from datetime import datetime
import subprocess
import tarfile
import os
import shutil
import paramiko as pm
import getpass
import ast
import sys
import resource
import gc
import io

try:
    import argcomplete
except ImportError:
    argcomplete = None

import cyclopts
from cyclopts.condor import dag as cdag
from cyclopts.condor import queue as cqueue
from cyclopts.condor import utils as cutils 
import cyclopts.tools as tools
import cyclopts.exchange_instance as inst
import cyclopts.params as params
import cyclopts.cyclopts_io as cycio
from cyclopts.problems import Solver

def condor_submit(args):
    # collect instance ids
    h5file = t.open_file(args.db, mode='r', filters=tools.FILTERS)
    instids = set(uuid.UUID(x).bytes for x in args.instids)
    rc = tools.parse_rc(args.rc) if args.rc is not None else tools.RunControl()
    fam = tools.get_obj(kind='family', rcs=tools.parse_rc(args.cycrc), 
                        args=args)
    path = '{0}/{1}'.format(fam.table_prefix, fam.property_table_name)
    instids = tools.collect_instids(h5file=h5file, path=path, rc=rc, 
                                    instids=instids)
    h5file.close()

    instids = [x.hex for x in instids]
    
    print('Submitting a {kind} job with {n} instances.'.format(
            kind=args.kind, n=len(instids)))
    # submit job
    if args.kind == 'dag':
        cdag.submit(args.user, args.db, instids, args.solvers,
                    host=args.host, remotedir=args.remotedir, 
                    keyfile=args.keyfile, verbose=args.verbose)
    elif args.kind == 'queue':
        cqueue.submit(args.user, args.db, instids, args.solvers, 
                      host=args.host, remotedir=args.remotedir, 
                      keyfile=args.keyfile, verbose=args.verbose,
                      nodes=args.nodes, port=args.port)        

def condor_collect(args):
    remotedir = '/'.join([tools.cyclopts_remote_run_dir, args.remotedir])
    print("Collecting the results of a condor run from {0} at {1}@{2}".format(
            remotedir, args.user, args.host))
    cutils.collect(args.localdir, remotedir, args.user, 
                   host=args.host, outdb=args.outdb,                 
                   clean=args.clean, keyfile=args.keyfile)

def condor_rm(args):
    print("Removing condor jobs for {0}@{1}".format(args.user, args.host))
    expr = 'work_queue_worker' if args.kind == 'workers' else None
    cutils.rm(args.user, host=args.host, keyfile=args.keyfile, expr=expr)
    
def cyclopts_combine(args):
    print("Combining {0} files into one master named {1}".format(
            len(args.files), args.outdb))
    tools.combine(iter(args.files), new_file=args.outdb, clean=args.clean)    

def convert(args):
    """Converts a contiguous dataspace as defined by an input run control file
    into problem instances in an HDF5 database. Each discrete point, as
    represented by a Sampler-type object is converted into a row in a table of
    the object's name, and each instance derived from data points is added to
    its relevant Instance data tables.
    """
    fin = args.rc
    fout = args.db
    ninst = args.ninst
    rc = tools.parse_rc(fin)
    verbose = args.verbose
    update_freq = args.update_freq
    debug = args.debug
    h5file = t.open_file(fout, 'a', filters=tools.FILTERS)

    obj_rcs = [rc, tools.parse_rc(args.cycrc)] \
        if os.path.exists(args.cycrc) else [rc]
    
    # conversion objects
    sp = tools.get_obj(kind='species', rcs=obj_rcs, args=args)
    fam = sp.family

    # table set up
    sp_manager = cycio.TableManager(h5file, 
                                    sp.register_tables(h5file, 
                                                       sp.table_prefix))
    fam_manager = cycio.TableManager(h5file, 
                                     fam.register_tables(h5file, 
                                                         fam.table_prefix))
    
    # convert
    n = 0
    sp.read_space(rc._dict)
    if verbose:
        print('{0} possible (not validated) points to be converted.'.format(
                sp.n_points))
    for point in sp.points():
        param_uuid = uuid.uuid4()
        sp.record_point(point, param_uuid, sp_manager.tables)
        for i in range(ninst):
            inst_uuid = uuid.uuid4()
            inst = sp.gen_inst(point)
            fam.record_inst(inst, inst_uuid, param_uuid, sp.name, 
                            fam_manager.tables)
            if verbose and n % update_freq == 0:
                print('{0} instances have been converted'.format(n))
            n += 1

    # clean up
    sp_manager.flush_tables()
    fam_manager.flush_tables()
    h5file.close()

def execute(args):
    indb = args.db
    outdb = args.outdb
    rc = tools.parse_rc(args.rc) if args.rc is not None else tools.RunControl()
    conds = ": ".join(args.conds.split(':'))
    asteval = ast.literal_eval(conds)
    if isinstance(asteval, basestring):
        # some scripting workflows produce a string the first time
        asteval = ast.literal_eval(asteval) 
    rc._update(asteval)
    solvers = args.solvers
    instids = set(uuid.UUID(x).bytes for x in args.instids)
    verbose = args.verbose

    obj_rcs = [rc, tools.parse_rc(args.cycrc)] \
        if os.path.exists(args.cycrc) else [rc]        
    
    if not os.path.exists(indb):
        raise IOError('Input database {0} does not exist.'.format(indb))

    # execution object
    fam = tools.get_obj(kind='family', rcs=obj_rcs, args=args)

    # get in/out dbs 
    h5in = t.open_file(indb, mode='r', filters=tools.FILTERS)
    if outdb is not None:
        h5out = t.open_file(outdb, mode='a', filters=tools.FILTERS)
    else:
        h5in.close()
        h5in = t.open_file(indb, mode='a', filters=tools.FILTERS)
        h5out = h5in

    # table set up
    in_manager = cycio.TableManager(h5in, 
                                    fam.register_tables(h5in, 
                                                        fam.table_prefix))
    out_manager = cycio.TableManager(h5out, 
                                     fam.register_tables(h5out, 
                                                         fam.table_prefix))
    result_tbl_name = 'Results'
    result_manager = cycio.TableManager(
        h5out, [cycio.ResultTable(h5out, path='/{0}'.format(result_tbl_name))])

    # get instids to run
    path = '{0}/{1}'.format(fam.table_prefix, fam.property_table_name)
    instids = tools.collect_instids(h5file=h5in, path=path, rc=rc, 
                                    instids=instids)
    if verbose: 
        print("Executing {0} instances.".format(len(instids)))

    # run each instance for each solver
    for instid in instids:
        inst = fam.read_inst(instid, in_manager.tables)
        for kind in solvers:
            solver = Solver(kind)
            if verbose:
                print('Solving instance {0} with the {1} solver'.format(
                        instid.hex, kind))
            soln = fam.run_inst(inst, solver)
            solnid = uuid.uuid4()
            fam.record_soln(soln, solnid, inst, instid, out_manager.tables)
            tbl = result_manager.tables[result_tbl_name]
            tbl.record_soln(soln, solnid, instid, solver)
            
    # clean up
    out_manager.flush_tables()
    result_manager.flush_tables()
    h5in.close()
    if h5out.isopen:
        h5out.close()

def update_cde(args):
    user = args.user
    host = args.host
    clean = args.clean
    keyfile = args.keyfile

    db = '.tmp.h5'
    
    shutil.copy(os.path.join(args.prefix, 'tests', 'files', 'obs_valid_in.h5'), 
                db)    
    cmd = "cde cyclopts exec --db {db} --solvers cbc greedy clp"
    cmd = cmd.format(db=db)
    subprocess.call(cmd.split(), shell=(os.name == 'nt'))

    pkgdir = 'cde-package'
    tarname = 'cde-cyclopts.tar.gz'

    print('tarring up', pkgdir)
    with tarfile.open(tarname, 'w:gz') as tar:
        tar.add(pkgdir)
    
    ffrom = tarname
    fto = '/'.join([cutils.batlab_base_dir_template.format(user=user), 
                    tarname])
    client = pm.SSHClient()
    client.set_missing_host_key_policy(pm.AutoAddPolicy())
    _, keyfile, pw = tools.ssh_test_connect(client, host, user, keyfile, auth=True)
    client.connect(host, username=user, key_filename=keyfile, password=pw)
    ftp = client.open_sftp()
    print("Copying {0} to {user}@{host}:{1}.".format(
            ffrom, fto, user=user, host=host))
    ftp.put(ffrom, fto)
    ftp.close()    
    client.close()

    if clean:
        rms = [tarname, db, 'cde.options']
        for rm in rms:
            os.remove(rm)
        shutil.rmtree(pkgdir)
    
def dump(args):
    """Dumps information about instances in a database"""
    h5file = t.open_file(args.db, mode='r', filters=tools.FILTERS)

    fam = tools.get_obj(kind='family', rcs=tools.parse_rc(args.cycrc), 
                        args=args)
    path = '{0}/{1}'.format(fam.table_prefix, fam.property_table_name)
    instids = tools.collect_instids(h5file=h5file, path=path)

    for iid in instids:
        print(iid.hex)

    h5file.close()

def main():
    """Entry point for Cyclopts runs."""
    parser = argparse.ArgumentParser("Cyclopts", add_help=True)    

    # parser for family info
    cyclopts_parser = argparse.ArgumentParser(add_help=False)
    cycrc = ('A global run control file, defaults to $HOME/.cyclopts.rc '
             'useful for declaring global family/species information.')
    cyclopts_parser.add_argument(
        '--cycrc', 
        default=os.path.expanduser(os.path.join('~', '.cyclopts.rc')),
        help=cycrc)
    family_parser = argparse.ArgumentParser(add_help=False)    
    fam_mod = ('The module for the problem family')
    family_parser.add_argument('--family_module', default=None, help=fam_mod)
    fam_class = ('The problem family class')
    family_parser.add_argument('--family_class', default=None, help=fam_class)
    
    # parser for species info
    species_parser = argparse.ArgumentParser(add_help=False)    
    sp_mod = ('The module for the problem species')
    species_parser.add_argument('--species_module', default=None, help=sp_mod)
    sp_class = ('The problem species class')
    species_parser.add_argument('--species_class', default=None, help=sp_class)
    
    sp = parser.add_subparsers()

    #
    # convert param space to database
    #
    converth = ("Convert a parameter space defined by an "
                "input run control file into an HDF5 database for a Cyclopts "
                "execution run.")
    conv_parser = sp.add_parser('convert', 
                                parents=[cyclopts_parser, species_parser], 
                                help=converth)
    conv_parser.set_defaults(func=convert)
    rc = ("The run control file to use that defines a continguous parameter space.")
    conv_parser.add_argument('--rc', dest='rc', help=rc)
    db = ("The HDF5 file to dump converted parameter space points to. "
            "This file can later be used an input to an execute run.")
    conv_parser.add_argument('--db', dest='db', default='cyclopts.h5', help=db)
    ninst = ("The number of problem instances to generate per point in "
             "parameter space.")
    conv_parser.add_argument('-n', '--ninstances', type=int, dest='ninst', 
                             default=1, help=ninst)
    count = ("Only read in the run control file and count the number of "
             "possible samplers that will be created.")
    conv_parser.add_argument('--count', dest='count_only', action='store_true', 
                             default=False, help=count)
    verbose = ("Print verbose output during the conversion process.")
    conv_parser.add_argument('-v', '--verbose', dest='verbose', 
                             action='store_true', default=False, help=verbose)
    debug = ("Use objgraph and pdb to debug the conversion process.")
    conv_parser.add_argument('--debug', dest='debug', 
                             action='store_true', default=False, help=debug)
    update_freq = ("The instance frequency with which to update stdout.")
    conv_parser.add_argument('-u', '--update-freq', type=int, dest='update_freq', 
                             default=100, help=update_freq)

    #
    # execute instances locally
    #
    exech = ("Executes a parameter sweep as defined "
             "by the input database and other command line arguments.")
    exec_parser = sp.add_parser('exec', 
                                parents=[cyclopts_parser, family_parser], 
                                help=exech)
    exec_parser.set_defaults(func=execute)
    db = ("An HDF5 Cyclopts database (e.g., the result of 'cyclopts convert').")
    exec_parser.add_argument('--db', dest='db', help=db)
    solversh = ("A list of which solvers to use.")
    exec_parser.add_argument('--solvers', nargs='*', default=['cbc'], 
                             dest='solvers', help=solversh)    
    instids = ("A list of instids (as UUID hex strings) to run.")
    exec_parser.add_argument('--instids', nargs='*', default=[], dest='instids', 
                             help=instids)    
    rch = ("The run control file, which allows idetification of a subset "
           "of input to run.")
    exec_parser.add_argument('--rc', dest='rc', default=None, help=rch)
    outdb = ("An optional database to write results to. By default, the "
             "database given by the --db flag is use.")
    exec_parser.add_argument('--outdb', dest='outdb', default=None, help=outdb)
    conds = ("A dictionary representation of execution conditions. This CLI "
             "argument can be used instead of placing them in an RC file.")
    exec_parser.add_argument('--conds', dest='conds', default='{}', help=conds)
    verbose = ("Print verbose output during execution.")
    exec_parser.add_argument('-v', '--verbose', dest='verbose', 
                             action='store_true', default=False, help=verbose)
        
    #
    # execute instances with condor
    #
    submit = ("Submits a job to condor, retrieves output when it has completed, "
               "and cleans up the condor user space after.")
    submit_parser = sp.add_parser('condor-submit', 
                                  parents=[cyclopts_parser, family_parser], 
                                  help=submit)
    submit_parser.set_defaults(func=condor_submit)
    
    # exec related
    submit_parser.add_argument('--rc', dest='rc', default=None, help=rch)
    submit_parser.add_argument('--db', dest='db', help=db)
    submit_parser.add_argument('--instids', nargs='*', default=[], dest='instids', 
                               help=instids)    
    submit_parser.add_argument('--solvers', nargs='*', default=['cbc'], 
                               dest='solvers', help=solversh)    
    
    # condor related
    uh = ("The condor user name.")
    submit_parser.add_argument('-u', '--user', dest='user', help=uh, 
                               default='gidden')
    hosth = ("The remote condor submit host.")
    submit_parser.add_argument('-t', '--host', dest='host', help=hosth, 
                               default='submit-3.chtc.wisc.edu')    
    keyfile = ("An ssh public key file.")
    submit_parser.add_argument('--keyfile', dest='keyfile', help=keyfile, 
                               default=None)    
    remotedir = ("The remote directory (relative to ~/cyclopts-runs)"
                 " on the submit node in which to run cyclopts jobs.")
    timestamp = "_".join([str(t) for t in datetime.now().timetuple()][:-3])
    submit_parser.add_argument(
        '-d', '--remotedir', dest='remotedir', help=remotedir, 
        default='run_{0}'.format(timestamp))      
    kind = ("The kind of condor submission to use.")
    submit_parser.add_argument('-k', '--kind', choices=['dag', 'queue'], 
                               default='queue', help=kind)
    port = ("The port to use for a condor queue submission.")
    submit_parser.add_argument('-p', '--port', default='5422', help=port)
    nodes = ("The execute nodes to target.")
    submit_parser.add_argument('--nodes', default=None, nargs='*', help=nodes)
    verbose = ("Print output during the submisison process.")
    submit_parser.add_argument('-v', '--verbose', dest='verbose', 
                               action='store_true', default=False, help=verbose)


    #
    # collect condor results
    #
    collect = ("Collects a condor submission's output.")
    collect_parser = sp.add_parser('condor-collect', help=collect)
    collect_parser.set_defaults(func=condor_collect)
    collect_parser.add_argument('--outdb', dest='outdb', 
                                default='cyclopts_results.h5', help=outdb)
    uh = ("The condor user name.")
    collect_parser.add_argument('-u', '--user', dest='user', help=uh, 
                                default='gidden')
    hosth = ("The remote condor submit host.")
    collect_parser.add_argument('-t', '--host', dest='host', help=hosth, 
                                default='submit-3.chtc.wisc.edu')    
    keyfile = ("An ssh public key file.")
    collect_parser.add_argument('--keyfile', dest='keyfile', help=keyfile, 
                                default=None)    
    localdir = ("The local directory in which to place resulting files.")
    collect_parser.add_argument('-l', '--localdir', dest='localdir',
                                help=localdir, default='.')     
    remotedir = ("The remote directory (relative to the user's home directory)"
                 " in which output files from a run are located.")
    collect_parser.add_argument('-d', '--remotedir', dest='remotedir', 
                                help=remotedir)      
    clean = ("Clean up the submit node after.")
    collect_parser.add_argument('--clean', dest='clean', help=clean,
                                action='store_true', default=False)    
    
    #
    # remove processes on condor
    #
    rm = ("Removes processes on condor for a user.")
    rm_parser = sp.add_parser('condor-rm', help=rm)
    rm_parser.set_defaults(func=condor_rm)
    uh = ("The condor user name.")
    rm_parser.add_argument('-u', '--user', dest='user', help=uh, 
                           default='gidden')
    hosth = ("The remote condor submit host.")
    rm_parser.add_argument('-t', '--host', dest='host', help=hosth, 
                           default='submit-3.chtc.wisc.edu')    
    keyfile = ("An ssh public key file.")
    rm_parser.add_argument('--keyfile', dest='keyfile', help=keyfile, 
                           default=None)    
    kind = ("The kind of job to remove.")
    rm_parser.add_argument('-k', '--kind', choices=['all', 'workers'], 
                           help=kind)
                
    #
    # build a cde tarball for condor
    #
    cde = ("Updates the Cyclopts CDE tarfile on a Condor submit node.")
    cde_parser = sp.add_parser('cde', 
                               parents=[cyclopts_parser, family_parser], 
                               help=cde)
    cde_parser.set_defaults(func=update_cde)

    # cde related
    uh = ("The cde user name.")
    source_path = ("The path to cyclopts source.")
    cde_parser.add_argument(
        '--source-path', 
        dest='prefix', 
        help=source_path, 
        default=os.path.expanduser(os.path.join('~', 'phd', 'cyclopts', 
                                                'cyclopts')))  
    cde_parser.add_argument('-u', '--user', dest='user', help=uh, 
                            default='gidden')
    hosth = ("The remote cde submit host.")
    cde_parser.add_argument('-t', '--host', dest='host', help=hosth, 
                            default='submit-3.chtc.wisc.edu')
    noclean = ("Do not clean up files.")
    cde_parser.add_argument('--no-clean', action='store_false', dest='clean', 
                            default=True, help=noclean)
    keyfile = ("An ssh public key file.")
    cde_parser.add_argument('--keyfile', dest='keyfile', help=keyfile, 
                               default=None)    
    
    #
    # combine a collection of databases
    #
    combine = ("Combines a collection of databases, merging their content.")
    combine_parser = sp.add_parser('combine', help=combine)
    combine_parser.set_defaults(func=cyclopts_combine)
    files = ("All files to combine.")
    combine_parser.add_argument('--files', nargs='+', dest='files', help=files)
    outdb = ("An output database, containing the combined content.")
    combine_parser.add_argument('-o', '--outdb', 
                                default='cyclopts_results.h5', dest='outdb', 
                                help=outdb)
    clean = ("Clean up (remove) the original files.")
    combine_parser.add_argument('--clean', dest='clean', help=clean,
                                action='store_true', default=False)    
                

    #
    # dump information about an instance db
    #
    dumph = ("Dumps information about an instance database.")
    dump_parser = sp.add_parser('dump', 
                                parents=[cyclopts_parser, family_parser], 
                                help=dumph)
    dump_parser.set_defaults(func=dump)
    dump_parser.add_argument('--db', dest='db', help=db)
    
    #
    # and away we go!
    #
    if argcomplete is not None:
        argcomplete.autocomplete(parser)
    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
