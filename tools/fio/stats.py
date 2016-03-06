import re
import argparse

def stats_result(result_file):
    with open(result_file) as rf:
        data = json.load(rf)
    for item in data:
        print item['data']


parser = argparse.ArgumentParser

parser.add_argument('-f', '--result_file', default='/tmp/fio.report', help='fio result file')

args = parser.parse_args()


