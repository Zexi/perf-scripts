#!/usr/bin/env python

# use influxdb to store test results
from influxdb import InfluxDBClient
from influxdb.client import InfluxDBClientError
from datetime import datetime
import time
import os

INFLUXDB_HOST = os.getenv('INFLUXDB_HOST', '127.0.0.1')
INFLUXDB_USER = os.getenv('INFLUXDB_USER', 'root')
INFLUXDB_PASS = os.getenv('INFLUXDB_PASS', 'root')
INFLUXDB_DBNAME = 'pst_results'
DIFF_SUB_TEST = ['sysbench']

def conn(host=INFLUXDB_HOST, port=8086, user=INFLUXDB_USER, password=INFLUXDB_PASS, db=INFLUXDB_DBNAME):
    return InfluxDBClient(host, port, user, password, db)

def create_db(client, db=INFLUXDB_DBNAME):
    dbs = client.get_list_database()
    if {'name': db} not in dbs:
        try:
            client.create_database(db)
        except InfluxDBClientError:
            # Drop and create
            client.drop_database(db)
            client.create_database(db)

    client.switch_database(db)

def insert_points(client, series):
    return client.write_points(series)

def gen_points(measuremnts_li, tags, time, fields_li):
    points = []
    num = len(measuremnts)
    for i in range(0, num):
        points.append(
                {
                    #"time": datetime.fromtimestamp(time).strftime("%Y-%m-%d %H:%M:%S"),
                    "time": int(int(datetime.fromtimestamp(start_time).strftime('%s')) * 1e9),
                    "measuremnts": measuremnts_li[i],
                    "fields": { fields_li[i] },
                    "tags": tags,
                    }
                )
        return points

def insert_rrdb_point(client, measuremnt, tags, start_time, fields):
    point_body = [
            {
                #"time": datetime.fromtimestamp(start_time).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "time": int(int(datetime.fromtimestamp(start_time).strftime('%s')) * 1e9),
                #"time": int(time.time()),
                "measurement": measuremnt,
                "tags": tags,
                "fields": dict(fields),
                }
            ]
    insert_points(client, point_body)
