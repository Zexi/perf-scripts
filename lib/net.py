import requests
import os
import sys

SRC = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))
LIB_PATH = SRC + '/lib'
sys.path.insert(0, LIB_PATH)
import job

def upload(url, _files, arguments={}):
    files = {}
    for _file in _files:
        files[os.path.basename(_file)] = open(_file, 'r')
    return requests.post(url, files=files, data=arguments)

def get_job_post_arguments(jobfile):
    job_post_arguments = {}
    job_obj = job.Job()
    job_obj.load(jobfile)
    job_post_arguments['testbox'] = job_obj['testbox']
    job_post_arguments['rootfs'] = job_obj['rootfs']
    job_post_arguments['commit'] = job_obj['commit']
    job_post_arguments['unit_job'] = job_obj['unit_job']
    job_post_arguments['start_time'] = job_obj['start_time']
    job_post_arguments['testcase'] = job_obj['testcase']
    job_post_arguments['job_params'] = job_obj['job_params']
    
    return job_post_arguments

def post_job(url, _files, jobfile):
    job_post_arguments = get_job_post_arguments(jobfile)
    r = upload(url, _files, job_post_arguments)
    print r.text
