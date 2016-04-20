#!/usr/bin/env python

import os
import sys
import subprocess

SRC = '/perf-scripts'
LIB_PATH = SRC + '/lib'
sys.path.insert(0, LIB_PATH)
import common

conf_file = SRC + '/etc/pst_server.yaml'
conf_dict = common.load_conf(conf_file)
conf_dict['pst_server']['port'] = os.getenv('PST_SERVER_PORT', 8080)
conf_dict['influxdb']['ip'] = os.getenv('INFLUXDB_HOST', '127.0.0.1')
conf_dict['influxdb']['port'] = os.getenv('INFLUXDB_PORT', 8086)
conf_dict['influxdb']['user'] = os.getenv('INFLUXDB_USER', 'root')
conf_dict['influxdb']['pass'] = os.getenv('INFLUXDB_PASS', 'root')
conf_dict['influxdb']['dbname'] = os.getenv('INFLUXDB_DBNAME', 'pst_results')

common.save_yaml(conf_file, conf_dict)

common.unify_localtime()
subprocess.call(SRC + '/server/server.py', shell=True)
