#!/usr/bin/env python2.7

import os
import sys
import re
import yaml
import shellwords
import datetime

SHELL_BLOCK_KEYWORDS = {
    "if": ['then', 'fi'], 
    "for": ['do', 'done'],
    "while": ['do', 'done'],
    "until": ['do', 'done'],
    "function": ['{', '}']
}

SRC = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))
TMP = '/tmp'
LIB_PATH = SRC + '/lib'
sys.path.insert(0, LIB_PATH)

import job

class Job2sh(object):

    def valid_shell_variable(self, key):
        return re.match(r'^[a-zA-Z_]+[a-zA-Z0-9_]*$', key)

    def shell_encode_keyword(self, key):
        return re.sub(r'[^a-z0-9_]', '_', key)

    def shell_escape_expand(self, val):
        if isinstance(val, list):
            val = '\n'.join(val)

        if not val:
            return ''
        elif isinstance(val, int):
            return str(val)
        elif isinstance(val, datetime.date) or re.match(r'^[-a-zA-Z0-9~!@#%^&*()_+=;:.,<>/?|\t "]+$', val):
            return "'%s'" % val
        elif re.match(r"^[-a-zA-Z0-9~!@#%^&*()_+=;:.,<>\/?|\t '$]+$", val):
            return '"' + val + '"'
        else:
            return 'no' + val + 'no'
            #return shellwords.ShellWords().

    def exec_line(self, line=None):
        if self.cur_func == "run_job":
            self.out_line(line)

    def out_line(self, line=None):
        if line == None:
            if len(self.script_lines) == 0:
                self.script_lines.append(line)
                return 
            if self.script_lines[-1] == None:
                return
            if re.match(r'^[\s{]*$', self.script_lines[-1]):
                return
            if re.match(r'^\s*(then|do)$', self.script_lines[-1]):
                return
        self.script_lines.append(line)

    def shell_header(self):
        self.out_line("#!/bin/bash")

    def get_program_env(self, program, env):
        program_env = {}
        args = []

        if not env:
            return program_env, args

        # expand predefined parameter set name
        if isinstance(env, basestring):
            if env in self.job_params:
                env = self.job_params[env]
            else:
                param_yaml = SRC + '/params/' + program + '.yaml'
                if os.path.exists(param_yaml):
                    with open(param_yaml) as f:
                        params = yaml.load(f)
                        if env in params:
                            env = params[env] 
        
        if isinstance(env, basestring):
            args = map(self.shell_escape_expand, shellwords.ShellWords().parse(env))
        if isinstance(env, int) or isinstance(env, float):
            args = str(env)
        if isinstance(env, dict):
            for k, v in env.items():
                if isinstance(v, dict):
                    for kk, vv in v.items():
                        program_env[kk] = vv
                else:
                    program_env[k] = v

        return program_env, args

    def create_cmd(self, program, args):
        program_path = self.programs_hash[program]

        if '/stats/' in program_path:
            args = []
        program_dir = os.path.dirname(program_path)
        wrapper = program_dir + '/wrapper'
        if os.access(wrapper, os.X_OK):
            cmd = [wrapper, program]
            cmd.extend(args)
        else:
            cmd = [program_path]
            cmd.extend(args)
        
        if re.search(r'/monitors', program_dir):
            cmd.insert(0, "run_monitor")
            if not re.search(r'run_monitor', self.script_lines[-1]):
                self.exec_line()
        elif re.search(r'/setup$', program_dir):
            cmd.insert(0, "run_setup")
            self.exec_line()
        elif re.search(r'/daemon$', program_dir):
            cmd.insert(0, "start_daemon")
            self.exec_line()
        elif re.search(r'/tests$', program_dir):
            cmd.insert(0, "run_test")
            self.exec_line()
            self.stats_lines.append('\t$SRC/stats/wrapper time %s.time' % program)
        else:
            self.exec_line()
        return cmd

    def shell_run_program(self, tabs, program, env):
        program_env, args = self.get_program_env(program, env)

        cmd = self.create_cmd(program, args)
        cmd_str = ' '.join(cmd)
        cmd_str = cmd_str.replace(SRC, r'$SRC')
        cmd_str = cmd_str.replace(TMP, r'$TMP')

        for k, v in program_env.items():
            self.exec_line(tabs + 'export ' + self.shell_encode_keyword(k) + "=" + self.shell_escape_expand(v))
        self.out_line(tabs  + cmd_str)
        for k, v in program_env.items():
            self.exec_line(tabs + 'unset ' + self.shell_encode_keyword(k))
 
    def shell_export_env(self, tabs, key, val):
        self.exec_line(tabs + "export %s=" % key + self.shell_escape_expand(val))

    def indent(self, ancestors):
        if ancestors == "extract_stats":
            return "\t" * 1
        else:
            return "\t" * (1 + len(ancestors))

    def parse_one(self, ancestors, key, val, pass_key):
        tabs = self.indent(ancestors)
        m = re.match(r'^script\s+(monitors|setup|tests|daemon|stats)/([-a-zA-Z0-9_/]+)$', key)
        m1 = re.match(r'^(function)\s+([a-zA-Z_]+[a-zA-Z_0-9]*)$', key)
        m2 = re.match(r'^(if|for|while|until)\s', key)
        if (key in self.programs_hash) or (re.match(r'(call|command|source)\s', key) and self.cur_func == "run_job"):
            if pass_key != "PASS_RUN_COMMANDS":
                return False
            self.shell_run_program(tabs, re.sub(r'^source\s+', '.', re.sub(r'^call\s+', '', key)), val)
            return "action_call_command"
        elif isinstance(val, basestring) and m:
            if not pass_key == "PASS_NEW_SCRIPT":
                return False 
            script_file = m.group(1) + '/' + m.group(2)
            script_name = os.path.basename(m.group(2))
            if self.cur_func == "run_job" and re.match(r'^(monitors|setup|tests|daemon)/', script_file) or self.cur_func == "extract_stats" and script_file.index('stats/') == 0:
                self.programs_hash[script_name] = SRC + '/' + script_file
            self.exec_line()
            self.exec_line(tabs + "cat > $SRC/%s" % script_file + "<<EOF")
            self.exec_line(val)
            self.exec_line("EOF")
            self.exec_line(tabs + "chmod +x $SRC/%S" % script_file)
            self.exec_line()
            return "action_new_script"
        elif isinstance(val, basestring) and m1:
            if not pass_key == "PASS_NEW_SCRIPT":
                return False
            shell_block = m1.group(1)
            func_name = m1.group(2)
            self.exec_line()
            self.exec_line(tabs + SHELL_BLOCK_KEYWORDS[shell_block][0])
            for l in val:
                self.exec_line("\t" + tabs + l)
            self.exec_line(tabs + SHELL_BLOCK_KEYWORDS[shell_block][1])
            return "action_new_function"
        elif isinstance(val, dict) and m2:
            if not pass_key == "PASS_RUN_COMMANDS":
                return False
            shell_block = m2.group(1)
            self.exec_line()
            self.exec_line(tabs + key)
            self.exec_line(tabs + SHELL_BLOCK_KEYWORDS[shell_block][0])
            self.parse_hash(ancestors + [key], val)
            self.exec_line(tabs + SHELL_BLOCK_KEYWORDS[shell_block][1])
            return "action_control_block"
        elif isinstance(val, dict):
            if not pass_key == "PASS_RUN_COMMANDS":
                return False
            self.exec_line()
            func_name = re.sub(r'[^a-zA-Z0-9_]', '_', key)
            self.exec_line(tabs + "%s()" % func_name)
            self.exec_line(tabs + "{")
            self.parse_hash(ancestors + [key], val)
            self.exec_line(tabs + "}\n")
            self.exec_line(tabs + "%s &" % func_name)
            return "action_background_function"
        elif self.valid_shell_variable(key):
            if not pass_key == "PASS_EXPORT_ENV":
                return False
            self.shell_export_env(tabs, key, val)
            return "action_export_env"
        return None

    def parse_job(self, ancestors, job_obj, pass_key):
        for key, val in job_obj.items():
            if self.parse_one(ancestors, key, val, pass_key):
                job_obj.pop(key)

    def parse_hash(self, ancestors, hash):
        nr_bg = 0
        for key, val in hash.items():
            self.parse_one(ancestors, key, val, "PASS_EXPORT_ENV")
        for key, val in hash.items():
            self.parse_one(ancestors, key, val, "PASS_NEW_SCRIPT")
        for key, val in hash.items():
            if self.parse_one(ancestors, key, val, "PASS_RUN_COMMANDS"):
                nr_bg += 1
        if nr_bg > 0:
            self.exec_line()
            #self.exec_line(self.indent(ancestors) + "wait")

    def job2sh(self, job_obj, out_script=sys.stdout):
        if 'params' not in job_obj:
            self.job_params = {}
        else:
            self.job_params = job_obj['params']

        self.script_lines = []
        self.stats_lines = []

        self.shell_header()

        self.cur_func = "run_job"

        self.out_line("export_top_env()")
        self.out_line("{")

        self.programs_hash = job.create_programs_hash("setup&monitors&tests&daemon")
        self.parse_job([], job_obj, "PASS_EXPORT_ENV")
        self.out_line()
        self.out_line('\t[ -n "$SRC" ] ||')
        self.out_line('\texport SRC=/perf-scripts/${user:-ps}/src')
        self.out_line('}\n\n')

        self.out_line("run_job()")
        self.out_line("{")
        self.out_line()
        self.out_line('\techo $$ > $TMP/run-job.pid')
        self.out_line()
        self.out_line('\t. $SRC/lib/job.sh')
        self.out_line('\t. $SRC/lib/env.sh')
        self.out_line()
        self.out_line('\texport_top_env')
        self.out_line()
        self.parse_hash([], job_obj)
        self.out_line('}\n\n')

        self.cur_func = "extract_stats"
        self.out_line("extract_stats()")
        self.out_line("{")
        self.programs_hash = job.create_programs_hash("stats")

        self.parse_hash([], job_obj)
        self.out_line()
        self.out_line(self.stats_lines)
        self.parse_hash([], yaml.load(open(SRC+'/etc/default_stats.yaml')))
        self.out_line("}\n\n")

        self.out_line('"$@"')

        for line in self.script_lines:
            if line:
                print(''.join(line))


