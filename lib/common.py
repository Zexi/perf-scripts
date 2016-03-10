#!/usr/bin/env python2.7

import yaml
import json
import shutil
import os
import sys
import collections

def dot_file(path):
    return os.path.dirname(path) + '/.' + os.path.basename(path)

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
