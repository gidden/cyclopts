#!/usr/bin/python

import operator
import os
import sys
import subprocess
import work_queue as wq
import io
import time

mv_sh = u"""#!/bin/bash
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

def running_workers(user):
    cmd = "condor_q {user} -run".format(user=user)
    print "executing cmd: {0}".format(cmd)
    p = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, shell=(os.name == 'nt'))
    inuse = [line.split('@')[1].split('.')[0] \
                 for line in p.stdout.readlines() if len(line.split('@')) > 1]
    return inuse

def idled_workers(user):
    inuse = []
    cmd = 'condor_q {user} -constraint JobStatus==1'.format(user=user)
    print "executing cmd: {0}".format(cmd)
    p = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, shell=(os.name == 'nt'))
    pids = [x.split()[0] for x in p.stdout.readlines() if \
                len(x.split()) > 0 and x.split()[0].split('.')[0].isdigit()]
    for pid in pids:
        cmd = 'condor_q {pid} -l'.format(pid=pid)
        print "executing cmd: {0}".format(cmd)
        p = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, shell=(os.name == 'nt'))
        req_line = [line for line in p.stdout.readlines() if line.startswith('Requirements')][0]
        s = req_line.split('machine == "')
        if len(s) > 1:
            inuse.append(s[1].split('.chtc.wisc.edu')[0])
    return inuse

def ncores(node):
    conds = 'machine=="{0}.chtc.wisc.edu"'.format(node)
    cmd = "condor_status -constraint {conds}".format(conds=conds)
    print "executing cmd: {0}".format(cmd)
    p = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, shell=(os.name == 'nt'))
    slots = [line for line in p.stdout.readlines() if line.startswith('slot') and '_' in line.split()[0].split('@')[0]]
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
    while n_assigned != n_tasks and n_assigned != all_cores:
        node = max(open_cores.iteritems(), key=operator.itemgetter(1))[0]
        n_assigned += 1
        workers[node] += 1
        open_cores[node] -= 1
    return dict((node, n) for node, n in workers.items() if n > 0)
    
def start_workers(worker_nodes, port):
    worker_cmd = """condor_submit_workers -r {conds} {machine}.chtc.wisc.edu {port} {n}"""
    print("Starting {0} workers.".format(sum(n for _, n in worker_nodes.items())))
    for node, n in worker_nodes.items():
        conds = '(ForGidden==true&&machine=="{0}.chtc.wisc.edu")'.format(node)
        cmd = worker_cmd.format(conds=conds, machine='submit-3', port=port, n=n)
        print "executing cmd: {0}".format(cmd)
        subprocess.call(cmd.split(), shell=(os.name == 'nt'))        

def mv_input(indb, path, nodes):
    pids = []
    shlines = mv_sh.format(loc=path)
    with io.open('mv.sh', 'w') as f:
        f.write(shlines)
    
    for node in nodes:
        conds = 'machine=="{0}.chtc.wisc.edu"'.format(node)
        sublines = mv_sub.format(indb=indb, node=node, conds=conds)
        subfile = 'mv_{0}.sub'.format(node)
        with io.open(subfile, 'w') as f:
            f.write(sublines)
            
        cmd = 'condor_submit {0}'.format(subfile)
        print "executing cmd for node {1}: {0}".format(cmd, node)
        p = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, shell=(os.name == 'nt'))
        pids.append(p.stdout.readlines()[1].split('cluster')[1].split('.')[0].strip())
        
    return pids

def rm_input(indb, path, nodes):
    pids = []
    shlines = rm_sh.format(loc=path)
    with io.open('rm.sh', 'w') as f:
        f.write(shlines)
    
    for node in nodes:
        conds = 'machine=="{0}.chtc.wisc.edu"'.format(node)
        sublines = rm_sub.format(indb=indb, node=node, conds=conds)
        subfile = 'rm_{0}.sub'.format(node)
        with io.open(subfile, 'w') as f:
            f.write(sublines)
            
        cmd = 'condor_submit {0}'.format(subfile)
        print "executing cmd for node {1}: {0}".format(cmd, node)
        p = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, shell=(os.name == 'nt'))
        pids.append(p.stdout.readlines()[1].split('cluster')[1].split('.')[0].strip())
        
    return pids

def wait_till_done(pids, timeout=5):
    done = False
    while not done:
        cmd = 'condor_q {0}'.format(" ".join(pids))
        print "executing cmd: {0}".format(cmd)
        p = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, shell=(os.name == 'nt'))
        out = p.stdout.readlines()
        if len(out) > 0 and not out[-1].strip().startswith('ID'):
            waiting = [x.split()[0] for x in out if \
                           len(x.split()) > 0 and x.split()[0].split('.')[0].isdigit()]
            print("Still waiting on jobs: {0}").format(" ".join(waiting))
            time.sleep(timeout)
        else:
            done = True
    print("All jobs are done")

def start_queue(q, n_tasks, idgen, indbpath, bring_files):
    runfile = bring_files['run_file']
    exec_cmd = """./{runfile} {outdb} {uuid} {path}"""
    q.specify_log('wq_log')
    for i in range(n_tasks):
        outdb = '{0}_out.h5'.format(i)
        cmd = exec_cmd.format(runfile=runfile, path=indbpath, uuid=idgen.next().strip(), outdb=outdb)
        t = wq.Task(cmd)
        t.specify_cores(1)
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
          print "task output: {0}".format(t.output)
          if t.return_status != 0:
            print "task failed: {0}".format(t.result)      
    print "all tasks complete!"

def main():
    port = 5522
    user = 'gidden'
    indb = 'instances.h5'
    indbpath = '../..' # relative to the landing point on the exec node
    exec_nodes = ['e125']#, 'e122', 'e123', 'e124', 'e125', 'e126']
    bring_files = {
#        'run_file': 'test-run.sh',
        'run_file': 'run.sh',
        'cyclopts_tar': '/home/gidden/cde-cyclopts.tar.gz', 
        'cde_tar': '/home/gidden/CDE.tar.gz',
        }
    nids = 2
    uuidfile = 'uuids'
    idgen = open(uuidfile)

    # get workers to launch    
    cores = open_cores(user, exec_nodes)
    workers = assign_workers(cores, n_tasks=1)

    # set up nodes with input
    pids = mv_input(indb, indbpath, workers.keys())
    timeout = 30 # 5 minutes
    wait_till_done(pids, timeout=timeout)
    
    # launch workers    
    start_workers(workers, port)
    
    # launch q
    print("Starting work queue master on port {0}".format(port))
    q = wq.WorkQueue(port)
    start_queue(q, nids, idgen, indbpath, bring_files)
    finish_queue(q)

    # tear down nodes with input    
    pids = rm_input(indb, indbpath, workers.keys())
    
    
    
if __name__ == '__main__':
    main()
