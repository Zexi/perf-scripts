import os
import sys
import subprocess
import time
import datetime
import re

SRC = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))
WORKSPACE = SRC + '/workspace'
LIB_PATH = SRC + '/lib'
sys.path.insert(0, LIB_PATH)
import common
import influxdb_pst

def update_influxdb(testcase_name, start_time, result_path, influxdb_client, influxdb_tags):
    if testcase_name == "fio-vm":
        testcase_name = 'fio'

    result_json_file = testcase_name + '.json'
    res, start_time = return_res_time(result_path, result_json_file, start_time)
    influxdb_pst.insert_point(influxdb_client, testcase_name, influxdb_tags, start_time, res)

def return_res_time(result_path, result_json_file, start_time):
    res = common.load_json(result_path.replace('"', '') + '/' + result_json_file)
    common.remove_res_point_arr(res)
    start_time = time.mktime(datetime.datetime.strptime(start_time, "%Y-%m-%d-%H:%M:%S").timetuple())
    return (res, start_time)
