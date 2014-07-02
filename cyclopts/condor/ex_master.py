#!/usr/bin/python

import os
import sys
import subprocess
import work_queue as wq

run_file = 'run.sh'

exec_cmd = """./{runfile} {outdb} {uuid}"""

uuids = ['a45c9977384b40eabfa8fb100bafa7a3', '38f60ce3843743cea713846da9381b22']

exec_nodes = ['e121', 'e122', 'e123', 'e124', 'e125', 'e126']

worker_cmd = """condor_submit_workers -r {conds} {machine}.chtc.wisc.edu {port} {n}"""

def running_workers(user):
    inuse = []
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
        inuse.append(req_line.split('machine == "')[1].split('.chtc.wisc.edu')[0])
    return inuse

def ncores(node):
    conds = 'machine=="{0}.chtc.wisc.edu"'.format(node)
    cmd = "condor_status -constraint {conds}".format(conds=conds)
    print "executing cmd: {0}".format(cmd)
    p = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, shell=(os.name == 'nt'))
    slots = [line for line in p.stdout.readlines() if line.startswith('slot') and '_' in line.split()[0].split('@')[0]]
    return len(slots)

def _choose_node(open_cores):
    for node, n in open_cores.items():
        if n > 0:
            return node

def start_workers(user, port, n_tasks = 1, n_leave_open = 0):
    current_workers = running_workers(user) + idled_workers(user)
    current_workers = dict((node, current_workers.count(node)) for node in exec_nodes) 

    open_cores = dict((node, max(ncores(node) - current_workers[node] - n_leave_open, 0)) for node in exec_nodes)
    all_cores = sum([n for _, n in open_cores.items()])

    n_started = 0
    while n_started != n_tasks and n_started != all_cores:
        node = _choose_node(open_cores)
        conds = '(ForGidden==true&&machine=="{0}.chtc.wisc.edu")'.format(node)
        cmd = worker_cmd.format(conds=conds, machine='submit-3', port=port, n=1)
        print "executing cmd: {0}".format(cmd)
        subprocess.call(cmd.split(), shell=(os.name == 'nt'))
        n_started += 1

def start_queue(q):
    cmds = [exec_cmd.format(runfile=run_file,
                            uuid=uuids[i], outdb='{0}_out.h5'.format(i)) for i in range(len(uuids))]
    
    takefiles = ['{0}_out.h5'.format(i) for i in range(len(uuids))]
    bringfiles = ['../cde-cyclopts.tar.gz', '../CDE.tar.gz', 'instances.h5', run_file]

    q.specify_log('wq_log')
    for cmd in cmds:
        t = wq.Task(cmd)
        t.specify_cores(1)
        for f in bringfiles:
            t.specify_input_file(f, os.path.basename(f))
        for f in takefiles:
            t.specify_output_file(f, os.path.basename(f))
        q.submit(t)
    
def finish_queue(q):
    print "waiting for tasks to complete..."
    while not q.empty():
      t = q.wait(5)
      print "listening on port: {0}".format(q.port)
      print "waiting on tasks, number: {0}".format(q.stats.tasks_waiting)
      print "active workers: {0}".format(q.stats.total_workers_joined)
      if t:
          print "task (id# %d) complete: %s (return code %d)" % (t.id, t.command, t.return_status)
          if t.return_status != 0:
            # The task failed. Error handling (e.g., resubmit with new parameters, examine logs, etc.) here
            print "task failed: {0}, host: {1}".format(t.result, t.hostname)
      
    #task object will be garbage collected by Python automatically when it goes out of scope
    print "all tasks complete!"

def main():
    port = 5422
    user = 'gidden'

    #q = wq.WorkQueue(port)
    #start_queue(q)
    start_workers(user, port, n_tasks=6)
    #finish_queue(q)

    open_cores = dict((node, ncores(node)) for node in exec_nodes)
    all_cores = sum([n for _, n in open_cores.items()])
    print open_cores
    print all_cores

if __name__ == '__main__':
    main()
