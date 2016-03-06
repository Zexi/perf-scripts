#!/usr/bin/env python2.7

import os
import sys
import argparse

SRC = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))
LIB_PATH = SRC + '/lib'
sys.path.insert(0, LIB_PATH)

import job
import job2sh
import yaml

parser = argparse.ArgumentParser()
parser.add_argument('-o', '--output', help="save shell script to FILE (default: stdout)", type=str)
parser.add_argument('-j', '--job', help="specify job file", type=str)

if len(sys.argv) == 1:
    parser.print_help()
    sys.exit(1)

args = parser.parse_args()

output_path = args.output
job_file = args.job

if not job_file:
    sys.stderr.write("Please specify job file")
    sys.exit(1)

with open(job_file, 'r') as f:
    job_obj = yaml.load(f)
j2s = job2sh.Job2sh()
j2s.job2sh(job_obj)

