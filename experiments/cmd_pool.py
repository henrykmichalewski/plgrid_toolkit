import traceback
from multiprocessing import Queue
import multiprocessing
import sys

# COOPIED FROM: https://sites.google.com/site/sachinkagarwal/home/code-snippets/parallelizing-multiprocessing-commands-using-python
from threading import Thread

import subprocess


def RunCommand(fullCmd):
    try:
        proc = subprocess.Popen(fullCmd, shell=True)
        outs, errs = proc.communicate()
    except:
        print(traceback.format_exc())
        return "Error executing command %s" % (fullCmd)


class Worker(Thread):
    def __init__(self,
                 work_queue,
                 result_queue,
                 ):
        # base class initialization
        Thread.__init__(self)
        self.work_queue = work_queue
        self.result_queue = result_queue
        self.kill_received = False

    def run(self):
        while (not (self.kill_received)) and (self.work_queue.empty() == False):
            try:
                job = self.work_queue.get_nowait()
            except:
                break

            (jobid, runCmd) = job
            rtnVal = (jobid, RunCommand(runCmd))
            #print('got result', jobid)
            #print rtnVal
            self.result_queue.put(rtnVal)


def execute_cmds(jobs_, num_processes=2):
    # load up work queue
    jobs = []
    for idx, job in enumerate(jobs_):
        jobs.append((idx, job))

    work_queue = multiprocessing.Queue()
    for job in jobs:
        work_queue.put(job)

    # create a queue to pass to workers to store the results
    result_queue = multiprocessing.Queue()

    # spawn workers
    worker = []
    for i in range(num_processes):
        worker.append(Worker(work_queue, result_queue))
        worker[i].start()

    # collect the results from the queue
    results = []
    while len(results) < len(jobs):  # Beware - if a job hangs, then the whole program will hang
        result = result_queue.get()
        results.append(result)

    results.sort()  # The tuples in result are sorted according to the first element - the jobid
    return (results)

if __name__ == '__main__':
    cmd = 'sleep 0.5; echo "fdsfs"; echo "dupa"'
    execute_cmds([cmd, cmd, cmd, cmd])