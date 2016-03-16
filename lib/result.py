import os
import sys
import subprocess
import rrdtool
import time
import datetime

SRC = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))
WORKSPACE = SRC + '/workspace'
RRDB_PATH = WORKSPACE + '/rrdb'
PIC_PATH = WORKSPACE +'/pics'
LIB_PATH = SRC + '/lib'
sys.path.insert(0, LIB_PATH)
import common

RRD_CREATE_OPTION = {"fio-vm": ['--step', '300', 'DS:srthr:GAUGE:600:U:U', 'DS:sriops:GAUGE:600:U:U',
                     'DS:rrthr:GAUGE:600:U:U', 'DS:rriops:GAUGE:600:U:U',
                     'DS:swthr:GAUGE:600:U:U', 'DS:swiops:GAUGE:600:U:U',
                     'DS:rwthr:GAUGE:600:U:U', 'DS:rwiops:GAUGE:600:U:U',
                     'RRA:AVERAGE:0.5:1:24']}

def update_rrdbs(testcase_name, rrdb_file, start_time, result_path):
    create_testcase_rrdb(testcase_name, rrdb_file, start_time)
    if testcase_name == "fio-vm":
        update_fio_vm_rrdb(rrdb_file, start_time, result_path)

def create_testcase_rrdb(testcase_name, rrdb_file, start_time):
    if not os.path.exists(rrdb_file):
        rrdb = rrdtool.create(rrdb_file, '--start', '%d' % (time.mktime(datetime.datetime.strptime(start_time, "%Y-%m-%d-%H:%M:%S").timetuple()) - 300), RRD_CREATE_OPTION[testcase_name])

def update_fio_vm_rrdb(rrdb_file, start_time, result_path):
    fio_res = common.load_json(result_path.replace('"', '') + '/fio.json')
    seq_read_throughput = fio_res['fio.seq_read.throughput'][0]
    seq_read_iops = fio_res['fio.seq_read.iops'][0]
    rand_read_throughput = fio_res['fio.rand_read.throughput'][0]
    rand_read_iops = fio_res['fio.rand_read.iops'][0]
    seq_write_throughput = fio_res['fio.seq_write.throughput'][0]
    seq_write_iops = fio_res['fio.seq_write.iops'][0]
    rand_write_throughput = fio_res['fio.rand_write.throughput'][0]
    rand_write_iops = fio_res['fio.rand_write.iops'][0]
    rrdupdate_cmd = "%d:%f:%f:%f:%f:%f:%f:%f:%f" % (time.mktime(datetime.datetime.strptime(start_time, "%Y-%m-%d-%H:%M:%S").timetuple()), seq_read_throughput, seq_read_iops, rand_read_throughput, rand_read_iops, seq_write_throughput, seq_write_iops, rand_write_throughput, rand_write_iops)
    rrdtool.update(rrdb_file, rrdupdate_cmd)

def plot_rrdbs(testcase_name):
    if not os.path.exists(PIC_PATH):
        os.makedirs(PIC_PATH, 02775)
    same_testcase_rrdbs = subprocess.check_output("find %s -regex '.*%s.*'" % (RRDB_PATH, testcase_name), shell=True).split()
    if testcase_name == 'fio-vm':
        for rrdb_file in same_testcase_rrdbs:
            plot_fio_vm(rrdb_file)

def plot_fio_vm(rrdb_file):
    pic = PIC_PATH + '/' + rrdb_file.split('/')[-1].replace('.rrd', '.png')
    cmd = "rrdtool graph %s --title 'Fio seq read/write throughput' DEF:srthr=%s:srthr:AVERAGE DEF:swthr=%s:swthr:AVERAGE LINE1:srthr#FF0000:'seq read iops' LINE2:swthr#00FF00:'seq write iops'" % (pic, rrdb_file, rrdb_file)
    subprocess.check_call(cmd, shell=True)
    return pic

