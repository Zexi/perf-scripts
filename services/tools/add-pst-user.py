#!/usr/bin/env python

import sys
import tornado
import tornado.ioloop
from motorengine import connect

sys.path.append('..')

from pst import secrets
from pservers import models

connect('pst')
io_loop = tornado.ioloop.IOLoop.current()
name = sys.argv[1]
email = sys.argv[2]
password = secrets.token_hex()

def handle_user_saved(user):
    try:
        assert user is not None
        print("Name: %s", user.to_son())
    finally:
        io_loop.stop()

def create_user(name, email, password, admin=True):
    kv = {'name': name, 'email': email, 'password': password, 'admin': admin}
    user = models.User(**kv)
    user.save(handle_user_saved)

io_loop.add_timeout(1, lambda: create_user(name, email, password))
io_loop.start()
