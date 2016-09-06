#!/usr/bin/env python
# -*-coding: utf-8 -*-

import datetime
import uuid

from motorengine.document import Document
from motorengine.fields import StringField, ListField, BooleanField, \
        JsonField

from fields import PsDateTimeField as DateTimeField
from pst.secrets import token_urlsafe


class TestBox(Document):
    __collection__ = "testboxs"

    box_id = StringField(required=True, default=lambda: uuid.uuid4().hex)
    hostname = StringField(required=True, max_length=200)
    password = StringField(required=True, max_length=200)
    created_at = DateTimeField(required=True)
    updated_at = DateTimeField(default=datetime.datetime.now)
    status = StringField(default='registered')
    tags = ListField(StringField(max_length=50))


class TestJob(Document):
    __collection__ = "testjobs"

    job_id = StringField(required=True, default=lambda: uuid.uuid4().hex)
    testcase = StringField(required=True)
    job_params = StringField(required=True)
    testbox = StringField(required=True)
    rootfs = StringField(required=True)
    commit = StringField(required=True)
    boxid = StringField(required=True)
    origin_desc = JsonField(required=True)
    desc = JsonField(required=True)
    created_at = DateTimeField(required=True)
    updated_at = DateTimeField(default=datetime.datetime.now)
    status = StringField(default='init')
    tags = ListField(StringField(max_length=50))


class User(Document):
    __collection__ = "users"

    email = StringField(required=True)
    name = StringField(required=True)
    password = StringField(required=True)
    admin = BooleanField(default=False)
    created_at = StringField(default=datetime.datetime.now().isoformat)
    token = StringField(default=lambda: token_urlsafe(16))

    def is_admin(self):
        return self.admin


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

    def create_user():
        user = User(name='zexi', email='zexi_li@yeah.net', admin=True, password='test')
        user.save(handle_user_saved)

    def handle_user_saved(user):
        try:
            assert user is not None
            assert user.name == 'zexi'
        finally:
            io_loop.stop()

    io_loop.add_timeout(1, create_user)
    io_loop.start()
