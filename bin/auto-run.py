#!/usr/bin/env python

import os
import sys
import schedule
import time
import subprocess
from lockfile import LockFile
from lockfile import LockTimeout

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

def run_shell_cmd(run_cmd):
    try:
        print("Run command: %s" % run_cmd)
        run_cmd_output = subprocess.check_output(run_cmd, stderr=subprocess.STDOUT, shell=True)
    except subprocess.CalledProcessError as exc:
        print("Status: FAIL", exc.returncode, exc.output)
    else:
        print("Output: \n{}\n".format(run_cmd_output))

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
    sync_dir = conf_dict.get('sync', {}).get('dir')
    sync_list = conf_dict.get('sync', {}).get('jobs')
    wait_timeout = conf_dict.get('sync', {}).get('timeout')
    for unit_jobfile in split_jobs_path:
        run_cmd = "%s run -j %s -u %s" % (SRC + '/bin/pst', unit_jobfile, uploadurl)
        # add lock to sync there, e.g. run doker and host test same time
        testcase_name = common.load_conf(unit_jobfile).get('testcase')
        if sync_dir and sync_list and testcase_name in sync_list:
            lock = LockFile(sync_dir + os.sep + testcase_name)
            try:
                lock.acquire(timeout=wait_timeout)
                run_shell_cmd(run_cmd)
                lock.release()
            except LockTimeout as e:
                print e
            except KeyboardInterrupt:
                if lock.is_locked():
                    lock.release()
        else:
            run_shell_cmd(run_cmd)
        print("Remove: %s" % unit_jobfile)
        os.remove(unit_jobfile)

common.unify_localtime()
conf_dict = common.load_conf(SRC + '/etc/autorun_conf.yaml')
uploadurl = get_upload_url(conf_dict)
schedule.every(conf_dict["runtime"]).seconds.do(run_each_job, conf_dict, uploadurl)

while True:
    schedule.run_pending()
    time.sleep(1)
