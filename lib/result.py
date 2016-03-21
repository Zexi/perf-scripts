import os
import sys
import subprocess
import rrdtool
import time
import datetime

SRC = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))
WORKSPACE = SRC + '/workspace'
RRDB_PATH = WORKSPACE + '/rrdb'
PIC_PATH = SRC + '/server/static/images'
LIB_PATH = SRC + '/lib'
sys.path.insert(0, LIB_PATH)
import common

RRD_CREATE_OPTION = {"fio-vm": ['--step', '300', 'DS:srthr:GAUGE:600:U:U', 'DS:sriops:GAUGE:600:U:U',
                     'DS:rrthr:GAUGE:600:U:U', 'DS:rriops:GAUGE:600:U:U',
                     'DS:swthr:GAUGE:600:U:U', 'DS:swiops:GAUGE:600:U:U',
                     'DS:rwthr:GAUGE:600:U:U', 'DS:rwiops:GAUGE:600:U:U',
                     'RRA:AVERAGE:0.5:1:600'],
                     "unixbench": ['--step', '1800', 'DS:score:GAUGE:3600:U:U',
                     'RRA:AVERAGE:0.5:1:120'],
                     "linpack": ['--step', '300', 'DS:score:GAUGE:600:U:U',
                     'RRA:AVERAGE:0.5:1:600'],
                     "superpi": ['--step', '300', 'DS:time:GAUGE:600:U:U',
                     'RRA:AVERAGE:0.5:1:600']
                     }

def update_rrdbs(testcase_name, rrdb_file, start_time, result_path):
    create_testcase_rrdb(testcase_name, rrdb_file, start_time)
    if testcase_name == "fio-vm":
        update_fio_vm_rrdb(rrdb_file, start_time, result_path)
    elif testcase_name == "unixbench":
        update_unixbench_rrdb(rrdb_file, start_time, result_path)

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

def update_unixbench_rrdb(rrdb_file, start_time, result_path):
    unixbench_res = common.load_json(result_path.replace('"', '') + '/unixbench.json')
    score = unixbench_res['unixbench.score'][0]
    rrdupdate_cmd = "%d:%f" % (time.mktime(datetime.datetime.strptime(start_time, "%Y-%m-%d-%H:%M:%S").timetuple()), score)
    rrdtool.update(rrdb_file, rrdupdate_cmd)

def update_superpi_rrdb(rrdb_file, start_time, result_path):
    unixbench_res = common.load_json(result_path.replace('"', '') + '/superpi.json')
    score = unixbench_res['superpi.Time'][0]
    rrdupdate_cmd = "%d:%f" % (time.mktime(datetime.datetime.strptime(start_time, "%Y-%m-%d-%H:%M:%S").timetuple()), score)
    rrdtool.update(rrdb_file, rrdupdate_cmd)

def plot_rrdbs(testcase_name):
    testcase_pic_path = PIC_PATH + '/' + testcase_name
    if not os.path.exists(testcase_pic_path):
        os.makedirs(testcase_pic_path, 02775)
    same_testcase_rrdbs = subprocess.check_output("find %s -regex '.*%s.*'" % (RRDB_PATH, testcase_name), shell=True).split()
    if testcase_name == 'fio-vm':
        for rrdb_file in same_testcase_rrdbs:
            plot_fio_vm(rrdb_file, testcase_pic_path)
    elif testcase_name == 'unixbench':
        for rrdb_file in same_testcase_rrdbs:
            plot_unixbench(rrdb_file, testcase_pic_path)
    elif testcase_name == 'superpi':
        for rrdb_file in same_testcase_rrdbs:
            plot_superpi(rrdb_file, testcase_pic_path)
    else:
        pass

def plot_fio_vm(rrdb_file, path):
    pic = path + '/' + rrdb_file.split('/')[-1].replace('.rrd', '.png')
    cmd = "rrdtool graph %s --title 'Fio seq read/write throughput' DEF:srthr=%s:srthr:AVERAGE DEF:swthr=%s:swthr:AVERAGE LINE1:srthr#FF0000:'seq read throughput' LINE2:swthr#00FF00:'seq write throughput'" % (pic, rrdb_file, rrdb_file)
    subprocess.check_call(cmd, shell=True)
    return pic

def plot_unixbench(rrdb_file, path):
    pic = path + '/' + rrdb_file.split('/')[-1].replace('.rrd', '.png')
    cmd = "rrdtool graph %s --title 'UnixBench score' DEF:score=%s:score:AVERAGE LINE1:score#FF0000:'score'" % (pic, rrdb_file)
    subprocess.check_call(cmd, shell=True)
    return pic

def plot_superpi(rrdb_file, path):
    pic = path + '/' + rrdb_file.split('/')[-1].replace('.rrd', '.png')
    cmd = "rrdtool graph %s --title 'SuperPI time' DEF:time=%s:time:AVERAGE LINE1:time#FF0000:'Run time'" % (pic, rrdb_file)
    subprocess.check_call(cmd, shell=True)
    return pic

def get_testcase_pic(path=PIC_PATH):
    testcases = [x.split('/')[-1] for x in subprocess.check_output('find %s -depth 1 -type d' % path, shell=True).split()]
    testcase_pics = {}
    for testcase in testcases:
        testcase_pics[testcase] = [x.split('static/')[-1] for x in subprocess.check_output("find %s -regex '.*png$'" % (path + '/' + testcase), shell=True).split()]

    return testcase_pics

if __name__ == "__main__":
    print get_testcase_pic()
