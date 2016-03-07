#!/usr/bin/env python2.7

import json
import argparse
import datetime
import os
import subprocess as subps

class FIOError(Exception): 
    pass


class FIOTimeout(Exception): 
    pass

def fio_test(filename, filesize, mode, bs, depth, ioengine, runtime): 

    fio_error_file = '/tmp/fio.err'
    fio_report_file = '/tmp/fio.report'

    if not os.path.exists(filename):
        open(filename, 'a').close()
    if not os.path.exists(fio_error_file):
        open(fio_error_file, 'a').close()

    try: 
        report = []

        for m in mode: 
            for b in bs: 
                for d in depth: 

                    cmd = 'python ./fio_conf_generator.py -n %s-%s-%s -f %s -s %sM -m %s -b %sK -d %s -e %s -t %s -o /tmp/fio.conf'\
                            % (m, b, d, filename, filesize, m, b, d, ioengine, runtime)
                    if subps.call(cmd.split(), stderr=file(fio_error_file, 'w')): 
                        raise FIOError()

                    utcnow = datetime.datetime.utcnow()
                    time_str = utcnow.strftime('%d: %m: %Y %H: %M: %S') 

                    with open('/tmp/fio.conf', 'r') as f: 
                        config = f.read()
                    cmd = 'sudo fio --timeout=%s --group_reporting --name=%s /tmp/fio.conf' % (runtime + 20, m)
                    try: 
                        out = subps.check_output(cmd, stderr=file(fio_error_file, 'w'), shell=True)
                        report.append({'datetime': time_str, 'config': config, 'data': out})
                    except Exception, e: 
                        with open(fio_error_file, 'r') as f: 
                            report.append({'datetime': time_str, 'config': config, 'error': '%s;%s' % (str(e), f.read())})

    except Exception, e: 
        with open(fio_error_file, 'r') as f: 
            report.append({'error': '%s;%s;%s' % (e.__class__.__name__, e, f.read())})

    finally: 
        with open(fio_report_file, 'w') as f: 
            f.write(json.dumps(report, indent=4, sort_keys=True))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('-f', '--file', default='/dev/vdc', help='file or device')
    parser.add_argument('-s', '--size', default=128, type=int, help='filesize in MB')
    parser.add_argument('-m', '--mode', nargs='+', type=str, default=['randrw'], help='mode <read|write|randread|randwrite|randrw>')
    parser.add_argument('-b', '--bs', nargs='+', type=int, default=[1], help='block size in KB')
    parser.add_argument('-d', '--depth', nargs='+', type=int, default=[1], help='iodepth')
    parser.add_argument('-t', '--runtime', type=int, default=30, help='runtime')
    parser.add_argument('-e', '--ioengine', type=str, default='libaio', help='io engine')

    args = parser.parse_args()

    fio_test(args.file, args.size, args.mode, args.bs, args.depth, args.ioengine, args.runtime)
