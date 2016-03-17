#!/usr/bin/env python2.7

import os
import sys
import schedule
import time
import yaml
import subprocess

SRC = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))
CYCLIC_PATH = SRC + '/workspace/cyclic-jobs/' 
LIB_PATH = SRC + '/lib'
sys.path.insert(0, LIB_PATH)
import job
import common

def get_cyclic_jobs(cyclic_file):
    with open(cyclic_file) as f:
        cyclic_jobs = yaml.load(f)
        return [SRC + '/jobs/' + path + '.yaml' for path in cyclic_jobs['jobs']]

def run_each_job():
    if not os.path.exists(CYCLIC_PATH):
        os.makedirs(CYCLIC_PATH, 02775)

    def split_run_job(job):
        job_params = job.path_params()
        unit_jobfile = prefix + '-' + job_params
        # there is a ['xxx', 'yyy'] bug in unit_jobfile, still not find it
        # maybe first jump it
        if '[' in unit_jobfile:
            return
        if 'commit' in job:
            unit_jobfile += '-' + job['commit']
        job['job_params'] = job_params
        job['unit_job'] = unit_jobfile.split('/')[-1]
        unit_jobfile += '.yaml'
        job.save(unit_jobfile)
        print "write to: %s" % unit_jobfile
        cmd = "%s run -j %s -u %s" % (SRC + '/bin/pst', unit_jobfile, uploadurl)
        subprocess.call(cmd, shell=True)

    cyclic_jobs_path = get_cyclic_jobs(SRC + '/etc/cyclic_jobs.yaml')
    uploadurl = "http://172.30.26.228:8080/post"
    for job_file_path in cyclic_jobs_path:
        job_obj = job.Job()
        job_obj.load(job_file_path)
        job_obj['enque_time'] = common.get_time()
        prefix = CYCLIC_PATH + os.path.splitext(os.path.basename(job_file_path))[0]
        job_obj.each_jobs(split_run_job)

schedule.every(6000).seconds.do(run_each_job)

while True:
    schedule.run_pending()
    time.sleep(1)
