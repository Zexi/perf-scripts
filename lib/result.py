import os
import sys
import subprocess
import rrdtool
import time
import datetime
import re

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
                     'RRA:AVERAGE:0.5:1:600'],

                     "ping": ['--step', '1500', 'DS:time:GAUGE:3000:U:U',
                     'RRA:AVERAGE:0.5:1:600'],

                     "mbw": ['--step', '300', 'DS:memcpy:GAUGE:600:U:U',
                     'DS:dumb:GAUGE:600:U:U', 'DS:mcblock:GAUGE:600:U:U',
                     'RRA:AVERAGE:0.5:1:600']
                     }

def update_rrdbs(testcase_name, rrdb_file, start_time, result_path):
    create_testcase_rrdb(testcase_name, rrdb_file, start_time)
    function_name = 'update_' + testcase_name.replace('-', '_') + '_rrdb'
    # call each testcase name function
    func = globals().get(function_name)
    if func:
        func(rrdb_file, start_time, result_path)
    else:
        pass

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
    res = common.load_json(result_path.replace('"', '') + '/superpi.json')
    pitime = res['superpi.Time'][0]
    rrdupdate_cmd = "%d:%f" % (time.mktime(datetime.datetime.strptime(start_time, "%Y-%m-%d-%H:%M:%S").timetuple()), pitime)
    rrdtool.update(rrdb_file, rrdupdate_cmd)

def update_ping_rrdb(rrdb_file, start_time, result_path):
    res = common.load_json(result_path.replace('"', '') + '/ping.json')
    pingtime = res['ping.avg_time'][0]
    rrdupdate_cmd = "%d:%f" % (time.mktime(datetime.datetime.strptime(start_time, "%Y-%m-%d-%H:%M:%S").timetuple()), pingtime)
    rrdtool.update(rrdb_file, rrdupdate_cmd)

def update_mbw_rrdb(rrdb_file, start_time, result_path):
    res = common.load_json(result_path.replace('"', '') + '/mbw.json')
    memcpy_bw = res['mbw.memcpy_avg'][0]
    dump_bw = res['mbw.dump_avg'][0]
    mcblock_bw = res['mbw.mcblock_avg'][0]

    rrdupdate_cmd = "%d:%f:%f:%f" % (time.mktime(datetime.datetime.strptime(start_time, "%Y-%m-%d-%H:%M:%S").timetuple()), memcpy_bw, dump_bw, mcblock_bw)
    rrdtool.update(rrdb_file, rrdupdate_cmd)

def plot_rrdbs(testcase_name):
    same_testcase_rrdbs = subprocess.check_output("find %s -regex '.*%s.*'" % (RRDB_PATH, testcase_name), shell=True).split()
    function_name = 'plot_' + testcase_name.replace('-', '_')
    # call each testcase name function
    func = globals().get(function_name)
    if func:
        func(same_testcase_rrdbs, testcase_name)
    else:
        pass

# decorator for each testcase plot
def plot(func):
    def wrapper(rrdb_files, testcase_name):
        testcase_pic_path = PIC_PATH + '/' + testcase_name
        if not os.path.exists(testcase_pic_path):
            os.makedirs(testcase_pic_path, 02775)
        pic_prefix = testcase_pic_path + '/' + testcase_name
        cmds = gen_cmds(rrdb_files, func())
        for index, cmd in enumerate(cmds):
            rrdtool.graph(pic_prefix+str(index)+'.png',
                          '--imgformat', 'PNG',
                          '--width', '600',
                          '--height', '400',
                          '--title', cmd["title"],
                          '--vertical-label', cmd["v-label"],
                          cmd["DEF"],
                          cmd["LINE"])
    return wrapper

def gen_each_cmd(rrdb_files, title, v_label, defcmds, linecmds):
    colors = [['FF0000', 'FF00FF'], ['006633', '660099']]
    defs = []
    lines = []
    hn_with_rrdb = [(x.split('--')[-1].replace('.rrd', ''), x) for x in rrdb_files]
    i = 0
    for hn, rrdb in hn_with_rrdb:
        hnv = re.sub(r'[-.]', '', hn)
        j = 0
        for cmd in defcmds:
            defs.append(cmd % (hnv, rrdb))
        for cmd in linecmds:
            lines.append(cmd % (hnv, colors[i][j], hn))
            j += 1
        i += 1
    return {"title": title, "v-label": v_label, "DEF": defs, "LINE": lines}

def gen_cmds(rrdb_files, will_plot_cmds):
    cmds = []
    for cmd_dict in will_plot_cmds:
        cmds.append(gen_each_cmd(rrdb_files, cmd_dict['title'], cmd_dict['v-label'], cmd_dict['def'], cmd_dict['line']))
    return cmds

@plot
def plot_fio_vm():
    will_plot_cmds = [{
        'title': 'Fio seq read/write throughput',
        'v-label': 'throughput KB/s',
        'def': ["DEF:%s_srthr=%s:srthr:AVERAGE", "DEF:%s_swthr=%s:swthr:AVERAGE"],
        'line': ["LINE1:%s_srthr#%s:%s seq read throughput", "LINE2:%s_swthr#%s:%s seq write throughput"]},

        {'title': 'Fio seq read/write iops',
        'v-label': 'iops',
        'def': ["DEF:%s_sriops=%s:sriops:AVERAGE", "DEF:%s_swiops=%s:swiops:AVERAGE"],
        'line': ["LINE1:%s_sriops#%s:%s seq read iops", "LINE2:%s_swiops#%s:%s seq write iops"]},

        {'title': 'Fio rand read/write throughput',
        'v-label': 'throughput KB/s',
        'def': ["DEF:%s_rrthr=%s:rrthr:AVERAGE", "DEF:%s_rwthr=%s:rwthr:AVERAGE"],
        'line': ["LINE1:%s_rrthr#%s:%s rand read throughput", "LINE2:%s_rwthr#%s:%s rand write throughput"]},

        {'title': 'Fio rand read/write iops',
        'v-label': 'iops',
        'def': ["DEF:%s_rriops=%s:rriops:AVERAGE", "DEF:%s_rwiops=%s:rwiops:AVERAGE"],
        'line': ["LINE1:%s_rriops#%s:%s rand read iops", "LINE2:%s_rwiops#%s:%s rand write iops"]}]

    return will_plot_cmds

@plot
def plot_unixbench():
    will_plot_cmds = [{
        'title': 'UnixBench score',
        'v-label': 'score',
        'def': ["DEF:%s_score=%s:score:AVERAGE"],
        'line': ["LINE1:%s_score#%s:%s score"]
        }]
    return will_plot_cmds

@plot
def plot_superpi():
    will_plot_cmds = [{
        'title': 'SuperPi compute 20 digits time',
        'v-label': 'time /s',
        'def': ["DEF:%s_time=%s:time:AVERAGE"],
        'line': ["LINE1:%s_time#%s:%s elapsed time"]}]

    return will_plot_cmds

@plot
def plot_ping():
    will_plot_cmds = [{
        'title': 'ping www.baidu.com time',
        'v-label': 'time /s',
        'def': ["DEF:%s_time=%s:time:AVERAGE"],
        'line': ["LINE1:%s_time#%s:%s elapsed time"]}]

    return will_plot_cmds

@plot
def plot_mbw():
    will_plot_cmds = [{
        'title': 'MEMCPY METHOD Bandwidth',
        'v-label': 'mem bandwidth MiB/s',
        'def': ["DEF:%s_memcpy=%s:memcpy:AVERAGE"],
        'line': ["LINE1:%s_memcpy#%s:%s memcpy method bandwidth"]},

        {'title': 'DUMB METHOD Bandwidth',
        'v-label': 'mem bandwidth MiB/s',
        'def': ["DEF:%s_dumb=%s:dumb:AVERAGE"],
        'line': ["LINE1:%s_dumb#%s:%s dumb method bandwidth"]},

        {'title': 'MCBLOCK METHOD Bandwidth',
        'v-label': 'mem bandwidth MiB/s',
        'def': ["DEF:%s_mcblock=%s:mcblock:AVERAGE"],
        'line': ["LINE1:%s_mcblock#%s:%s mcblock method bandwidth"]}]

    return will_plot_cmds

def get_testcase_pic(path=PIC_PATH):
    testcases = [x.split('/')[-1] for x in subprocess.check_output('find %s -mindepth 1 -maxdepth 1 -type d' % path, shell=True).split()]
    testcase_pics = {}
    for testcase in testcases:
        testcase_pics[testcase] = [x.split('static/')[-1] for x in subprocess.check_output("find %s -regex '.*png$'" % (path + '/' + testcase), shell=True).split()]

    return testcase_pics

if __name__ == "__main__":
    print get_testcase_pic()
