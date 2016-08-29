#!/usr/bin/env python

# -*- coding: utf-8 -*-

import sys
import time
import errno
import socket

PORT_COUNT_DEFAULT=30

if len(sys.argv) < 2:
    print('Usage: %s addr [port_count]' % sys.argv[0])
    sys.exit(1)
addr = sys.argv[1]
port_count = PORT_COUNT_DEFAULT

if len(sys.argv) >= 3:
    port_count = int(sys.argv[2])

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    status = 'unknown'
    time_begin = time.time()
    port = 10000 + (int(time_begin / 50) % port_count) # change port per 50 sec
    s.connect((addr, port))
    status = 'connected'
except (socket.error, IOError, OSError) as e:
    if e.args[0] == errno.ECONNREFUSED:
        status = 'refused'
finally:
    time_end = time.time()
    print '%s %.3f' % (status, (time_end - time_begin) * 1000)
    s.close()
