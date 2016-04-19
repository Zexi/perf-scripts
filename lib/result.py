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

def update_influxdb(testcase_name, start_time, result_path, influxdb_client, influxdb_tags, job_params=None):
    if job_params:
        suffix = (testcase_name + '_' + job_params).replace('-', '_')
    else:
        suffix = testcase_name.replace('-', '_')
    function_name = 'update_' + suffix + '_db'
    # call each testcase name function
    func = globals().get(function_name)
    if func:
        func(start_time, result_path, influxdb_client, influxdb_tags)
    else:
        pass

def return_res_time(result_path, result_json_file, start_time):
    res = common.load_json(result_path.replace('"', '') + '/' + result_json_file)
    common.remove_res_point_arr(res)
    start_time = time.mktime(datetime.datetime.strptime(start_time, "%Y-%m-%d-%H:%M:%S").timetuple())
    return (res, start_time)

def update_fio_vm_db(start_time, result_path, influxdb_client, influxdb_tags):
    fio_res, start_time = return_res_time(result_path, 'fio.json', start_time)
    influxdb_pst.insert_point(influxdb_client, "fio", influxdb_tags, start_time, fio_res)

def update_unixbench_db(start_time, result_path, influxdb_client, influxdb_tags):
    res, start_time = return_res_time(result_path, 'unixbench.json', start_time)
    influxdb_pst.insert_point(influxdb_client, "unixbench", influxdb_tags, start_time, res)

def update_superpi_db(start_time, result_path, influxdb_client, influxdb_tags):
    res, start_time = return_res_time(result_path, 'superpi.json', start_time)
    influxdb_pst.insert_point(influxdb_client, "superpi", influxdb_tags, start_time, res)

def update_ping_db(start_time, result_path, influxdb_client, influxdb_tags):
    res, start_time = return_res_time(result_path, 'ping.json', start_time)
    influxdb_pst.insert_point(influxdb_client, "ping", influxdb_tags, start_time, res)

def update_mbw_db(start_time, result_path, influxdb_client, influxdb_tags):
    res, start_time = return_res_time(result_path, 'mbw.json', start_time)
    influxdb_pst.insert_point(influxdb_client, "mbw", influxdb_tags, start_time, res)

def update_sysbench_cpu_db(start_time, result_path, influxdb_client, influxdb_tags):
    res, start_time = return_res_time(result_path, 'sysbench.json', start_time)
    influxdb_pst.insert_point(influxdb_client, "sysbench", influxdb_tags, start_time, res)

def update_sysbench_oltp_db(start_time, result_path, influxdb_client, influxdb_tags):
    res, start_time = return_res_time(result_path, 'sysbench.json', start_time)
    influxdb_pst.insert_point(influxdb_client, "sysbench", influxdb_tags, start_time, res)
