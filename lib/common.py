#!/usr/bin/env python2.7

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
