#!/usr/bin/env python

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

def get_cyclic_jobs(conf_dict):
    return [SRC + '/jobs/' + path + '.yaml' for path in conf_dict['jobs']]

def get_upload_url(conf_dit):
    def load_server_conf(conf_dict):
        server_conf = conf_dict['server']
        url = 'http://%s:%s/%s' % (server_conf['hostname'], server_conf['port'], server_conf['res'])
        return url
    return load_server_conf(conf_dict)

def load_conf(conf_file):
    with open(conf_file) as f:
        conf_dict = yaml.load(f)
        return conf_dict

def run_each_job(conf_dict):
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

    cyclic_jobs_path = get_cyclic_jobs(conf_dict)
    uploadurl = get_upload_url(conf_dict)
    for job_file_path in cyclic_jobs_path:
        job_obj = job.Job()
        job_obj.load_head("%s/hosts/%s" % (SRC, os.getenv("HOSTNAME")))
        job_obj.load(job_file_path)
        job_obj['enque_time'] = common.get_time()
        prefix = CYCLIC_PATH + os.path.splitext(os.path.basename(job_file_path))[0]
        job_obj.each_jobs(split_run_job)

common.unify_localtime()
conf_dict = load_conf(SRC + '/etc/autorun_conf.yaml')
schedule.every(conf_dict["runtime"]).seconds.do(run_each_job, conf_dict)

while True:
    schedule.run_pending()
    time.sleep(1)
