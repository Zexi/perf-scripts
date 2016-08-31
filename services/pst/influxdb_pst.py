#!/usr/bin/env python

# use influxdb to store test results
from influxdb import InfluxDBClient
from influxdb.client import InfluxDBClientError
from datetime import datetime


def conn(host, port, user, password, db):
    return InfluxDBClient(host, port, user, password, db)


def create_db(client, db):
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


def gen_points(measuremnts_li, tags, start_time, fields_li):
    points = []
    num = len(measuremnts_li)
    for i in range(0, num):
        points.append(
                {
                    "time": int(int(datetime.fromtimestamp(start_time).strftime('%s')) * 1e9),
                    "measuremnts": measuremnts_li[i],
                    "fields": {fields_li[i]},
                    "tags": tags,
                    }
                )
        return points


def insert_point(client, measuremnt, tags, start_time, fields):
    point_body = [
            {
                "time": int(int(datetime.fromtimestamp(start_time).strftime('%s')) * 1e9),
                "measurement": measuremnt,
                "tags": tags,
                "fields": dict(fields),
                }
            ]
    insert_points(client, point_body)
