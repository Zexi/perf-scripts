#!/usr/bin/env python

import yaml
import json
import shutil
import os
import sys
import collections
import tarfile
import tempfile
import pytz
from datetime import datetime
import subprocess

SRC = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)) 

def unify_time(tz):
    timezone = pytz.timezone(tz)
    return timezone.normalize(pytz.utc.localize(datetime.utcnow()).astimezone(timezone))

def get_time(tz='Asia/Shanghai'):
    return unify_time(tz).strftime('%Y-%m-%d %H:%M:%S')

def unify_localtime(tz='Asia/Shanghai'):
    localtime = '/etc/localtime'
    if tz not in os.path.realpath(localtime):
        os.remove(localtime)
        os.symlink('/usr/share/zoneinfo/' + tz, localtime)

def dot_file(path):
    return os.path.dirname(path) + '/.' + os.path.basename(path)

def get_filepaths(directory):
    file_paths = []
    for root, directories, files in os.walk(directory):
        for filename in files:
            filepath = os.path.join(root, filename)
            file_paths.append(filepath)
    return file_paths

def create_tar_gz(directory):
    file_paths = get_filepaths(directory)
    tar = tarfile.open(tempfile.mktemp(prefix="pst-", suffix=".tar.gz"), "w:gz")
    for path in file_paths:
        tar.add(path)
    tar.close()
    return tar.name

def extract_tar_gz(src, dst):
    tar = tarfile.open(src)
    tar.extractall(dst)
    tar.close()

def save_json(obj, file):
    temp_file = dot_file(file) + "-" +  str(os.getpid())
    with open(temp_file, 'w') as f:
        f.write(json.dumps(obj, indent=4))
    shutil.move(temp_file, file)

def load_json(file):
    if os.path.exists(file):
        with open(file, 'r') as f:
            return json.load(f, object_pairs_hook=collections.OrderedDict)
    else:
        sys.stderr.write(file + " not exists")
        return None

def to_json(obj):
    return json.dumps(obj)

def is_in_docker():
    check_file = "/proc/self/cgroup"
    in_docker = False
    with open(check_file) as f:
        for line in f:
            if line.split('/')[1] == 'docker':
                in_docker = True
                break
    return in_docker

def is_in_vm():
    check_cmd = "grep -q -w hypervisor /proc/cpuinfo"
    try:
        subprocess.check_call(check_cmd, shell=True)
    except subprocess.CalledProcessError:
        return False
    else:
        return True

def get_hostname():
    hostname = os.environ.get('HOSTNAME')
    if not hostname:
        hostname = subprocess.check_output('hostname', shell=True).strip('\n')
    return hostname

def get_cpu_info():
    cmd = 'cat /proc/cpuinfo'
    cpu_hash = {}
    for line in [line.split(':') for line in subprocess.check_output(cmd, shell=True).strip().split("\n") if line]:
        k, v = line
        cpu_hash[k.replace('\t', '')] = v
    return cpu_hash

def get_mem_size():
    if is_in_docker():
        check_file = '/sys/fs/cgroup/memory/memory.limit_in_bytes'
        kB = int(open(check_file, 'r').readline().strip()) / 1024
    else:
        cmd = "grep MemTotal /proc/meminfo | awk '{print $2}'"
        kB = int(subprocess.check_output(cmd, shell=True).strip())
    return kB

def create_host_config(hostname):
    conf_dir = SRC + '/hosts'
    if not os.path.exists(conf_dir):
        os.mkdir(conf_dir)
    conf_file = conf_dir + '/' + hostname

    host_dict = {}
    if os.path.exists(conf_file):
        with open(conf_file, 'r') as f:
            host_dict.update(yaml.load(f))

    # judge testbox host type
    if is_in_vm():
        host_dict['type'] = 'vm'
    elif is_in_docker():
        host_dict['type'] = 'docker'
    else:
        host_dict['type'] = 'pm'

    cpu_info = get_cpu_info()
    mem_size = get_mem_size()
    host_dict['memory'] = '%dK' % mem_size
    host_dict['cpu_model_name'] = cpu_info['model name']
    host_dict['cpu_freq'] = cpu_info['cpu MHz']

    with open(conf_file, 'w') as f:
        f.write(yaml.dump(host_dict, default_flow_style=False))

def remove_res_point_arr(res):
    for k, v in res.iteritems():
        if isinstance(v[0], basestring):
            res[k] = v[0]
            continue
        v = [float(x) for x in v]
        if len(v) > 3:
            v.remove(min(v))
            v.remove(max(v))
        res[k] = sum(v) / len(v)

def load_conf(conf_file):
    with open(conf_file) as f:
        conf_dict = yaml.load(f)
        return conf_dict

def save_yaml(conf_file, conf_dict):
    with open(conf_file, 'w') as f:
        f.write(yaml.dump(conf_dict, default_flow_style=False))
