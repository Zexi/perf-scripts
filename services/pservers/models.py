#!/usr/bin/env python
# -*-coding: utf-8 -*-

import datetime
import uuid

from motorengine.document import Document
from motorengine.fields import StringField, DateTimeField, \
        ListField, BooleanField


class TestBox(Document):
    __collection__ = "testboxs"

    box_id = StringField(required=True, default=lambda: uuid.uuid4().hex)
    hostname = StringField(required=True, max_length=200)
    created_at = StringField(default=datetime.datetime.now().isoformat)
    updated_at = StringField(default=datetime.datetime.now().isoformat)
    status = StringField(default=datetime.datetime.now().isoformat)
    tags = ListField(StringField(max_length=50))


class User(Document):
    __collection__ = "users"

    email = StringField(required=True)
    name = StringField(required=True)
    password = StringField(required=True)
    admin = BooleanField()
    created_at = DateTimeField(default=datetime.datetime.now)


if __name__ == '__main__':
    import tornado
    import tornado.ioloop
    from motorengine import connect
    connect('pst')
    io_loop = tornado.ioloop.IOLoop.current()

    def create_testbox():
        tsb = TestBox(hostname='tbox1', box_id=1)
        tsb.save(handle_testbox_saved)

    def handle_testbox_saved(tsb):
        try:
            assert tsb is not None
            assert tsb.box_id == 1
        finally:
            io_loop.stop()

    io_loop.add_timeout(1, create_testbox)
    io_loop.start()
