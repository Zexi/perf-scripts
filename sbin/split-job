#!/usr/bin/env python2.7

import os
import sys
import argparse

SRC = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))
LIB_PATH = SRC + '/lib'
sys.path.insert(0, LIB_PATH)

import job
import pytz
from datetime import datetime

#import ipdb

def unify_time(tz):
    timezone = pytz.timezone(tz)
    return timezone.normalize(pytz.utc.localize(datetime.utcnow()).astimezone(timezone))

def get_time(tz='Asia/Shanghai'):
    return unify_time(tz).strftime('%Y-%m-%d %H:%M:%S')

parser = argparse.ArgumentParser()
parser.add_argument('-o', '--output', help="output path", type=str)
parser.add_argument('--no-defaults', help="do not load the defaults headers", type=str, default="no")
parser.add_argument('-j', '--jobs', help="specify job files", nargs='+', type=str)

if len(sys.argv) == 1:
    parser.print_help()
    sys.exit(1)

args = parser.parse_args()
print args

output_path = args.output
if not output_path:
    sys.stderr.write(r"Use '-o' to specify output path" + '\n')
    sys.exit(1)
elif not os.path.isdir(output_path):
    sys.stderr.write("%s: no such direcotory\n" % output_path)
    sys.exit(1)

opt_testbox = os.getenv("HOSTNAME")
atom_jobs = []

def test_func(job):
    unit_jobfile = prefix + '-' + job.path_params()
    if 'commit' in job:
        unit_jobfile += '-' + job['commit']
    unit_jobfile += '.yaml'
    job.save(unit_jobfile)
    print "%s => %s" % (jobfile, unit_jobfile)

for jobfile in args.jobs:
    jobs = job.Job()

    #if args.no_defaults == "no":
    #ipdb.set_trace()
    #jobs.load_head("%s/jobs/DEFAULTS" % SRC)

    jobs.load(jobfile)

    jobs.job['enque_time'] = get_time()
    prefix = args.output + os.sep + os.path.splitext(os.path.basename(jobfile))[0]

    jobs.each_jobs(test_func)

