#!/usr/bin/env python

'''
This script will auto install the specified jobs defined in etc/autorun_conf.yaml
'''

import os
import sys
import yaml
import subprocess

SRC = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))

def load_conf(conf_file):
    with open(conf_file) as f:
        conf_dict = yaml.load(f)
        return conf_dict

def get_cyclic_jobs(conf_dict):
    return [SRC + '/jobs/' + path + '.yaml' for path in conf_dict['jobs']]

def install_jobs(conf_file):
    conf_dict = load_conf(conf_file)
    jobs = ' '.join(get_cyclic_jobs(conf_dict))
    cmd = '%s/bin/pst install %s' % (SRC, jobs)
    subprocess.call(cmd, shell=True)

install_jobs(SRC + '/etc/autorun_conf.yaml')
