#!/usr/bin/env python

import os
import sys
import subprocess

SRC = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))
LIB_PATH = SRC + '/lib'
sys.path.insert(0, LIB_PATH)
import common

print "--------------------------------"
# install mysql and configure it
cmds = []
cmds.append('echo "mysql-server-5.6 mysql-server/root_password password pass" | debconf-set-selections')
cmds.append('echo "mysql-server-5.6 mysql-server/root_password_again password pass" | debconf-set-selections')
cmds.append('apt-get -y install mysql-server-5.6')
cmds.append('mysql -u root -ppass -e "create database test"')
for cmd in cmds:
    subprocess.check_call(cmd, shell=True)

common.unify_localtime()
