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
    cpu_freq = get_cpu_info()['cpu MHz']
    mem_size = get_mem_size()

    with open(conf_file, 'w') as f:
        f.write('memory: %dK\n' % mem_size)
        f.write('cpu_freq: %sMHz\n' % cpu_freq)
