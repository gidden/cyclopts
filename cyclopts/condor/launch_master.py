#!/usr/bin/python

import operator
import os
import sys
import subprocess
import work_queue as wq
import io
import time
import re
import math

mv_sh = u"""#!/bin/bash
echo "pwd: $PWD"
echo "dbdir: $PWD/{loc}"
ls -l {loc}
mv $1 {loc}
ls -l {loc}
"""

mv_sub = u"""universe = vanilla
executable = mv.sh
arguments = {indb}
output = mv_{node}.out
error = mv_{node}.err
log = mv_{node}.log
requirements = {conds}
should_transfer_files = YES
when_to_transfer_output = ON_EXIT
request_cpus = 1
transfer_input_files = {indb}
notification = never
queue
"""

rm_sh = u"""#!/bin/bash
echo "pwd: $PWD"
echo "dbdir: $PWD/{loc}"
ls -l {loc}
rm {loc}/$1
ls -l {loc}
"""

rm_sub = u"""universe = vanilla
executable = rm.sh
arguments = {indb}
output = rm_{node}.out
error = rm_{node}.err
log = rm_{node}.log
requirements = {conds}
request_cpus = 1
notification = never
queue
"""

def mem_per_core(units='kB'):
    """returns memory per core in kb (default) or another desired unit"""
    with io.open('/proc/meminfo') as f:
        lines = [x for x in f.readlines() \
                     if re.search('MemTotal', x) is not None]
    mem = float(lines[0].split()[1]) # memory in kb
    with io.open('/proc/cpuinfo') as f:
        lines = [x for x in f.readlines() \
                     if re.search('processor', x) is not None]
    ncores = len(lines)
    mpc = mem / ncores
    if units.lower() == 'mb':
        mpc *= 1e6 / 1e9 # MB to kB
    return int(math.floor(mpc))

def condor_cmd(cmd, timeout=10):
    rtn = -1
    while rtn != 0:
        print "executing cmd: {0}".format(cmd)
        p = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, shell=(os.name == 'nt'))
        out, err = p.communicate()
        rtn = p.returncode
        if rtn != 0:
            print "cmd failed with code {0}, trying again in {1} seconds".format(rtn, timeout)
            time.sleep(timeout)
    return out.split('\n')

def running_workers(user):
    cmd = "condor_q {user} -run".format(user=user)
    lines = condor_cmd(cmd)
    inuse = [line.split('@')[1].split('.')[0] \
                 for line in lines if len(line.split('@')) > 1]
    return inuse

def idled_workers(user):
    inuse = []
    cmd = 'condor_q {user} -constraint JobStatus==1'.format(user=user)
    lines = condor_cmd(cmd)
    pids = [x.split()[0] for x in lines if \
                len(x.split()) > 0 and x.split()[0].split('.')[0].isdigit()]
    for pid in pids:
        cmd = 'condor_q {pid} -l'.format(pid=pid)
        lines = condor_cmd(cmd)
        req_line = [line for line in lines if line.startswith('Requirements')][0]
        s = req_line.split('machine == "')
        if len(s) > 1:
            inuse.append(s[1].split('.chtc.wisc.edu')[0])
    return inuse

def ncores(node):
    conds = 'machine=="{0}.chtc.wisc.edu"'.format(node)
    cmd = "condor_status -constraint {conds}".format(conds=conds)
    lines = condor_cmd(cmd)
    if len(lines) > 1 and 'Drained' in lines[2]:
        return 0
    slots = [line for line in lines if line.startswith('slot') and '_' in line.split()[0].split('@')[0]]
    return len(slots)

def open_cores(user, exec_nodes, n_leave_open=0):
    current_workers = running_workers(user) + idled_workers(user)
    current_workers = dict((node, current_workers.count(node)) for node in exec_nodes) 
    open_cores = dict((node, max(ncores(node) - current_workers[node] - n_leave_open, 0)) for node in exec_nodes)
    return open_cores

def assign_workers(open_cores, n_tasks=1):
    workers = dict((node, 0) for node, _ in open_cores.items())
    all_cores = sum([n for _, n in open_cores.items()])
    n_assigned = 0
    to_assign = min(n_tasks, all_cores)
    while n_assigned != to_assign:
        node = max(open_cores.iteritems(), key=operator.itemgetter(1))[0]
        n_assigned += 1
        workers[node] += 1
        open_cores[node] -= 1
    return dict((node, n) for node, n in workers.items() if n > 0)

#
# this function can be used if there are future slow downs
#
def assign_workers_new(open_cores, n_tasks=1, n_threads=16, use_max_threads=True):
    if n_tasks > n_threads * len(open_cores) and use_max_threads: 
        # use the bazooka
        return dict((n, n_threads) for n in open_cores.keys())
    
    # be more precise
    to_assign = min(n_tasks, sum(open_cores.values()))
    # don't use defaultdict -- python on htcondor is old
    workers = dict((n, 0) for n in open_cores.keys())
    n_assigned = 0
    while n_assigned != to_assign:
        # get node with most available threads
        node = max(open_cores.iteritems(), key=operator.itemgetter(1))[0]
        n_assigned += 1
        workers[node] += 1
        open_cores[node] -= 1
    return dict((k, v) for k, v in workers.iteritems() if v > 0)

def _start_workers(node, n, port, memory=None):
    cmd_pre = ("""condor_submit_workers -t 600 --cores 1""")
    cmd_post = ("""{machine}.chtc.wisc.edu {port} {n}""") # machine is the submit node

    # fill in pre
    if memory is not None:
        cmd_pre = '{0} --memory {1}'.format(cmd_pre, memory)
    conds = '(machine=="{0}.chtc.wisc.edu")'.format(node) # machine is the exec node
    cmd_pre = '{0} -r {1}'.format(cmd_pre, conds)

    # fill in post
    cmd_post = cmd_post.format(machine='submit-3', port=port, n=n)
    
    cmd = " ".join([cmd_pre, cmd_post])
    print("Starting {0} workers or node {1}.".format(n, node))
    print "executing cmd: {0}".format(cmd)
    subprocess.call(cmd.split(), shell=(os.name == 'nt'))

def start_workers(pids, worker_nodes, port, memory=None, timeout=5):
    done = False
    started = set()
    nodes = dict((pid, node) for node, pid in pids.iteritems())
    pids = set(pids.values())
    if memory is None:
        memory = int(math.floor(125 * 1e3 / 16.0)) # 125 GB per 16 cores (in Mbs)
    while not done:
        cmd = 'condor_q {0}'.format(" ".join(pids))
        out = condor_cmd(cmd)
        if len(out) > 0 and not out[-1].strip().startswith('ID'):
            waiting = set(x.split()[0].split('.')[0] for x in out if \
                              len(x.split()) > 0 and x.split()[0].split('.')[0].isdigit())
            tostart = pids - waiting - started
            for pid in tostart:
                node = nodes[pid]
                _start_workers(node, worker_nodes[node], port, memory=memory)
                started.add(pid)
            if len(waiting) == 0:
                done = True
            else:
                print("Still waiting on jobs: {0}").format(" ".join(waiting))
                time.sleep(timeout)
        else:
            done = True
    print("All jobs are done")

def write_mv(indb, path, nodes):
    shlines = mv_sh.format(loc=path)
    with io.open('mv.sh', 'w') as f:
        f.write(shlines)    
    for node in nodes:
        conds = 'machine=="{0}.chtc.wisc.edu"'.format(node)
        sublines = mv_sub.format(indb=indb, node=node, conds=conds)
        subfile = 'mv_{0}.sub'.format(node)
        with io.open(subfile, 'w') as f:
            f.write(sublines)
    
def exec_mv(nodes):
    pids = {}    
    for node in nodes:
        subfile = 'mv_{0}.sub'.format(node)
        cmd = 'condor_submit {0}'.format(subfile)
        lines = condor_cmd(cmd)
        pids[node] = lines[1].split('cluster')[1].split('.')[0].strip()
    return pids

def write_rm(indb, path, nodes):
    shlines = rm_sh.format(loc=path)
    with io.open('rm.sh', 'w') as f:
        f.write(shlines)
    for node in nodes:
        conds = 'machine=="{0}.chtc.wisc.edu"'.format(node)
        sublines = rm_sub.format(indb=indb, node=node, conds=conds)
        subfile = 'rm_{0}.sub'.format(node)
        with io.open(subfile, 'w') as f:
            f.write(sublines)

def exec_rm(nodes):
    pids = {}
    for node in nodes:
        subfile = 'rm_{0}.sub'.format(node)
        cmd = 'condor_submit {0}'.format(subfile)
        lines = condor_cmd(cmd)
        pids[node] = lines[1].split('cluster')[1].split('.')[0].strip()    
    return pids

def start_queue(q, n_tasks, idgen, indb, bring_files, memory=None):
    runfile = bring_files['run_file']
    exec_cmd = """./{runfile} {outdb} {uuid} {indb}"""
    if memory is None:
        memory = int(math.floor(125 * 1e3 / 16.0)) # 125 GB per 16 cores (in Mbs)
    for i in range(n_tasks):
        outdb = '{0}_out.h5'.format(i)
        cmd = exec_cmd.format(runfile=runfile, indb=indb, uuid=idgen.next().strip(), outdb=outdb)
        t = wq.Task(cmd)
        t.specify_cores(1) # 1 core
        t.specify_memory(memory)
        f = bring_files['cyclopts_tar']
        t.specify_input_file(f, os.path.basename(f), cache=True)
        f = bring_files['cde_tar']
        t.specify_input_file(f, os.path.basename(f), cache=True)
        f = runfile
        t.specify_input_file(f, os.path.basename(f), cache=False)
        t.specify_output_file(outdb, outdb, cache=False)
        q.submit(t)
    
def finish_queue(q):
    print "waiting for tasks to complete..."
    while not q.empty():
      t = q.wait(5)
      print "listening on port: {0}".format(q.port)
      print "waiting on tasks, number: {0}".format(q.stats.tasks_waiting)
      print "active workers: {0}".format(q.stats.total_workers_joined)
      if t:
          print "task (id# %d) on host %s complete: %s (return code %d)" % (t.id, t.hostname, t.command, t.return_status)
          #print "task output: {0}".format(t.output)
          if t.return_status != 0:
            print "task failed: {0}".format(t.result)      
    print "all tasks complete!"

def main():
    print('Work Queue Master script has been launched with pid: {0}').format(
        os.getpid())

    # get vars from command line or use defaults
    args = [a.split('=') for a in sys.argv[1:]]
    args = dict((a[0], a[1]) for a in args)

    # generally specify
    port = 5222 if 'port' not in args.keys() else int(args['port'])
    user = 'gidden' if 'user' not in args.keys() else args['user']
    indb = 'instances.h5' if 'indb' not in args.keys() else args['indb']
    indbpath = '../..' # relative to the landing point on the exec node
    exec_nodes = ['e121', 'e122', 'e123', 'e124', 'e125', 'e126'] \
        if 'nodes' not in args.keys() else args['nodes'].split(',')
    nids = 2 if 'nids' not in args.keys() else int(args['nids'])
    memory = None if 'memory' not in args.keys() else float(args['memory'])
    log = False if 'log' not in args.keys() else bool(args['log'])
    run_file = 'run.sh' if 'run_file' not in args.keys() else args['run_file']
    uuidfile = 'uuids' if 'uuids' not in args.keys() else args['uuids']
    
    msg = 'logging output' if log else 'not logging output'
    print(msg)
    
    idgen = open(uuidfile)
    bring_files = {
        'run_file': run_file,
        'cyclopts_tar': '/home/gidden/cde-cyclopts-exec.tar.gz', 
        'cde_tar': '/home/gidden/CDE.tar.gz',
        }

    # get workers to launch  
    cores = open_cores(user, exec_nodes)
    workers = assign_workers_new(cores, n_tasks=nids)
    if sum([n for _, n in workers.iteritems()]) == 0:
        raise ValueError("No available cores for workers were found")
    config = ", ".join(["{0}: {1}".format(node, n) for node, n in workers.iteritems()])
    print("Assigning {0} tasks to workers in the following configuration: {1}".format(
            nids, config))
    
    # write mv/rm files
    write_mv(indb, indbpath, workers.keys())
    write_rm(indb, indbpath, workers.keys())

    # set up nodes with input
    pids = exec_mv(workers.keys())
    timeout = 60 * 3 # 3 minutes
    
    # launch q
    print("Starting work queue master on port {0}".format(port))
    q = wq.WorkQueue(port)
    if log:
        q.specify_log("queue.log")
        q.enable_monitoring("tasks.log");
    start_queue(q, nids, idgen, '/'.join([indbpath, indb]), bring_files, memory=memory)

    # wait till each mv is done and then launch its workers
    start_workers(pids, workers, port, memory=memory, timeout=timeout)    

    # wait till its done
    finish_queue(q)

    # tear down nodes with input    
    pids = exec_rm(workers.keys())    
    
if __name__ == '__main__':
    main()
