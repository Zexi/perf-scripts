#!/usr/bin/env python

import os
import sys
import schedule
import time
import yaml
import subprocess

SRC = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))
CYCLIC_PATH = SRC + '/workspace/cyclic-jobs'
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

def run_each_job(conf_dict, uploadurl):
    if not os.path.exists(CYCLIC_PATH):
        os.makedirs(CYCLIC_PATH, 02775)

    # split each cyclic jobs
    cyclic_jobs_path = get_cyclic_jobs(conf_dict)
    split_job_params = ' '.join(cyclic_jobs_path)
    split_cmd = "%s split -j %s -o %s" % (SRC+'/bin/pst', split_job_params, CYCLIC_PATH)
    split_output = subprocess.check_output(split_cmd, shell=True)
    split_jobs_path = [split_file.split(' => ')[1] for split_file in split_output.split('\n') if split_file]

    # run each splited jobs
    for unit_jobfile in split_jobs_path:
        run_cmd = "%s run -j %s -u %s" % (SRC + '/bin/pst', unit_jobfile, uploadurl)
        try:
            print("Run command: %s" % run_cmd)
            run_cmd_output = subprocess.check_output(run_cmd, stderr=subprocess.STDOUT, shell=True)
        except subprocess.CalledProcessError as exc:
            print("Status: FAIL", exc.returncode, exc.output)
        else:
            print("Output: \n{}\n".format(run_cmd_output))
        finally:
            print("Remove: %s" % unit_jobfile)
            os.remove(unit_jobfile)

common.unify_localtime()
conf_dict = load_conf(SRC + '/etc/autorun_conf.yaml')
uploadurl = get_upload_url(conf_dict)
schedule.every(conf_dict["runtime"]).seconds.do(run_each_job, conf_dict, uploadurl)

while True:
    schedule.run_pending()
    time.sleep(1)
