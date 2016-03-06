#!/usr/bin/env python2.7
import yaml
import os
import sys
import types
import shutil
import commands

import ipdb

SRC = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))

def __create_programs_hash(dir_list, src):

    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    programs = {}
    for dirname in dir_list:
        for dirpath, dirnames, files in os.walk(src + os.sep + dirname):
            for f in files:
                path = os.path.join(dirpath, f)
                if os.path.isdir(path):
                    continue
                if not is_exe(path):
                    continue
                filen = os.path.basename(path)
                if filen == 'wrapper':
                    continue
                if programs.has_key(filen):
                    sys.stderr.write("Conflict names %s and %s\n" % (programs[filen], path))
                    continue
                programs[filen] = path

    return programs

def create_programs_hash(dir_str, src=SRC):
    programs_cache = {}
    if dir_str in programs_cache:
        programs = programs_cache[dir_str]

    programs = __create_programs_hash(dir_str.split('&'), src)
    programs_cache[dir_str] = programs
    return programs

def for_each_in(ah, sets, func):
    for k, v in ah.iteritems():
        if k in sets:
            func(ah, k, v)
        if isinstance(v, types.DictType):
            for_each_in(v, sets, func)

def atomic_save_yaml(obj, filepath):
    tmp_file = filepath + "-" + str(os.getpid())
    with open(tmp_file, 'w') as stream:
        stream.write(yaml.dump(obj, default_flow_style=False))
    shutil.move(tmp_file, filepath)

EXPAND_DIMS = ['kconfig', 'commit', 'rootfs', 'boot_params']

class Job(dict):

    def __init__(self, *arg, **kw):
        super(Job, self).__init__(*arg, **kw)

    def update(self, hash, top=False):
        if not hasattr(self, 'job'):
            self.job = {}
        if top:
            self.job = self.job.update(hash)
        else:
            self.job.update(hash)

    def load_head(self, jobfile, top=False):
        jobfile = self.abspath(jobfile)
        if not os.path.exists(jobfile):
            return 
        with open(jobfile) as stream:
            job = yaml.load(stream)
            self.update(job, top)

    def load(self, jobfile):
        with open(self.abspath(jobfile)) as stream:
            tmp_job = yaml.load(stream)
            if not hasattr(self, 'job'):
                self.job = {}
            self.job.update(tmp_job)

    def abspath(self, path):
        return os.path.abspath(path)

    def init_program_options(self):
        self.program_options = {'boot_params': '-'}

        def program_options_func(h, k, v):
            for line in commands.getoutput(SRC + os.sep + 'bin/program-options ' + self.programs[k]).split('\n'):
                if line:
                    type1, name = line.split()
                    self.program_options[name] = type1
                    print 'self.program_options: name: %s type: %s' % (name, type1)

        for_each_in(self.job, self.programs, program_options_func)

    def each_job_init(self):
        self.programs = create_programs_hash("setup&tests&daemon", SRC)
        self.init_program_options()
        self.dims_to_expand = set(EXPAND_DIMS)
        self.dims_to_expand |= set(self.programs.keys())
        self.dims_to_expand |= set(self.program_options.keys())

    def each_job(self, func):
        self.each_job_func_point = func

        def each_job_func(h, k, v):
            if isinstance(v, types.ListType):
                for vv in v:
                    h[k] = vv
                    self.each_job(func)

                h[k] = v
                return

        for_each_in(self.job, self.dims_to_expand, each_job_func)
        func(self)

    def each_jobs(self, func):
        self.each_job_init()
        #ipdb.set_trace()
        self.each_job(func)

    def each_param(self, func):

        def each_param_func(h, k, v):
            if isinstance(v, types.DictType):
                return
            func(k, v, self.program_options.get(k))

        self.programs = create_programs_hash("setup&tests&daemon", SRC)
        self.init_program_options()

        for_each_in(self.job, dict(self.programs.items()+self.program_options.items()), each_param_func)

    def path_params(self):

        def path_params_func(k, v, option_type):
            if option_type == '=':
                if v and v != '':
                    self.path += "%s=$s" % (k, v)
                else:
                    self.path += "%s" % k
                self.path += '-'
                return
            if not v:
                return
            self.path += str(v)
            self.path += '-'

        self.path = ''
        self.each_param(path_params_func)
        if not self.path:
            return 'defaults'
        else:
            return self.path

    def save(self, jobfile):
        atomic_save_yaml(self.job, jobfile)
