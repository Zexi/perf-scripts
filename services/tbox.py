#!/usr/bin/env python

import os
import os.path
import tornado
import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.options

from tornado.options import define, options

from pst import common
from tboxs.testcase import TestEnv
from tboxs.task import TaskManager

PST_SRC = os.getenv('PST_SRC', common.PST_SRC)
define("port", default=8686, help="run on the given port", type=int)
define("run_job_files", default=[PST_SRC+'/etc/autorun_conf.yaml'],
       multiple=True, help="specify run jos' files")


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r'/', MainHandler),
        ]
        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), 'tboxs/templates'),
            static_path=os.path.join(os.path.dirname(__file__), 'tboxs/static'),
            debug=True,)
        self.test_env_list = [TestEnv(run_job_file) for run_job_file
                              in options.run_job_files]
        super(Application, self).__init__(handlers, **settings)


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
    global _default_testenv_list
    tornado.options.parse_command_line()
    app = Application()
    _default_testenv_list = app.test_env_list
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(options.port)
    TaskManager(_default_testenv_list).start()
    tornado.ioloop.IOLoop.current().start()

if __name__ == "__main__":
    os.environ['PST_MAIL_SUBJECT'] = u"[PST Testbox][log]"
    import pst.manlog
    logger = pst.manlog.logger
    main()
