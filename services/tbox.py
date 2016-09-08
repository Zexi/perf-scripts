#!/usr/bin/env python

import os
import os.path
import json
import tornado
import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.options

from tornado.options import define, options
from tornado_json.application import Application
from tornado_json.routes import get_routes

from pst import common
from tboxs.testcase import TestEnv
from tboxs.task import TaskManager

PST_SRC = os.getenv('PST_SRC', common.PST_SRC)
define("port", default=8686, help="run on the given port", type=int)
define("run_job_files", default=[PST_SRC+'/etc/autorun_conf.yaml'],
       multiple=True, help="specify run jos' files")


class TboxApp(Application):
    def __init__(self, api_routes, db_conn=None, generate_docs=False):
        routes = [
            (r'/', MainHandler),
        ]
        routes += api_routes
        print("Routes\n========\n\n" + json.dumps(
            [(url, repr(rh)) for url, rh in routes],
            indent=2
        ))
        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), 'tboxs/templates'),
            static_path=os.path.join(os.path.dirname(__file__), 'tboxs/static'),
            debug=True,)
        self.test_env_list = [TestEnv(run_job_file) for run_job_file
                              in options.run_job_files]
        super(TboxApp, self).__init__(routes, settings, db_conn, generate_docs)


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        test_env_list = self.application.test_env_list
        self.render(
            'index.html',
            page_title="Pstbox | Home",
            header_text="All running testcase",
            test_env_list=test_env_list
        )

_default_testenv_list = None


def main():
    import tboxs
    global _default_testenv_list
    tornado.options.parse_command_line()
    app = TboxApp(get_routes(tboxs))
    _default_testenv_list = app.test_env_list
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(options.port, address='127.0.0.1')
    TaskManager(_default_testenv_list).start()
    tornado.ioloop.IOLoop.current().start()

if __name__ == "__main__":
    os.environ['PST_MAIL_SUBJECT'] = u"[PST Testbox][log]"
    import pst.manlog
    logger = pst.manlog.logger
    main()
