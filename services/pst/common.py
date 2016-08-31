#!/usr/bin/env python

import os
import sys
import yaml
import json
import shutil
import collections
import tarfile
import tempfile
import subprocess
import pytz
from datetime import datetime


def unify_time(tz):
    timezone = pytz.timezone(tz)
    return timezone.normalize(
        pytz.utc.localize(datetime.utcnow()).astimezone(timezone))


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
    tar = tarfile.open(tempfile.mktemp(
        prefix="pst-", suffix=".tar.gz"), "w:gz")
    for path in file_paths:
        tar.add(path)
    tar.close()
    return tar.name


def extract_tar_gz(src, dst):
    tar = tarfile.open(src)
    tar.extractall(dst)
    tar.close()


def load_json(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return json.load(f, object_pairs_hook=collections.OrderedDict)
    else:
        sys.stderr.write(file_path + " not exists")
        return None


def save_json(obj, file_path):
    temp_file = dot_file(file_path) + "-" + str(os.getpid())
    with open(temp_file, 'w') as f:
        f.write(json.dumps(obj, indent=4))
    shutil.move(temp_file, file_path)


def to_json(obj):
    return json.dumps(obj)


def load_yaml(file_path):
    with open(file_path) as f:
        dic = yaml.load(f)
        return dic


def create_dir(path):
    if not os.path.exists(path):
        os.makedirs(path, 02775)


def run_cmd(cmd, shell=False):
    import logging
    logger = logging.getLogger(__name__)
    try:
        logger.info("Run command: %s" % cmd)
        res = subprocess.check_output(
            cmd, stderr=subprocess.STDOUT, shell=shell)
        return res
    except subprocess.CalledProcessError, ex:
        logger.error(
            "FAIL: Run command: %s"
            "message: %s\nreturncode: %s\n output: %s\n"
            % (ex.cmd, ex.message, ex.returncode, ex.output))
        raise


def get_hostname():
    hostname = os.environ.get('HOSTNAME')
    if not hostname:
        hostname = run_cmd('hostname', shell=True).strip('\n')
    return hostname


def get_commit():
    return run_cmd('uname -r', shell=True).strip('\n')


def parent_dir(path, steps=0):
    from os.path import dirname
    parent_dir = dirname(path)
    for x in range(0, steps):
        parent_dir = dirname(parent_dir)
    return parent_dir

PST_SRC = parent_dir(os.path.abspath(__file__), 2)


def get_rootfs():
    cmd = '. %s/lib/detect-system.sh; detect_system; \
            echo $_system_name_lowercase' % PST_SRC
    return run_cmd(cmd, shell=True).strip('\n')


def is_in_docker():
    check_file = "/proc/self/cgroup"
    in_docker = False
    if not os.path.exists(check_file):
        return in_docker
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


def get_cpu_info():
    cmd = 'cat /proc/cpuinfo'
    cpu_hash = {}
    for line in [line.split(':') for line
                 in run_cmd(cmd, shell=True).strip().split("\n") if line]:
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
