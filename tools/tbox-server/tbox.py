#!/usr/bin/env python

import os
import os.path
import time
import logging
import tornado
import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.options

from tornado import gen
from tornado.options import define, options
from tornado.concurrent import run_on_executor, futures

from pstbox import common
from pstbox.testcase import TestEnv

MAX_WORKERS = 4
PST_SRC = os.getenv('PST_SRC', common.parent_dir(os.path.abspath(__file__), 2))
TIMEFORMAT = '%Y-%m-%d-%X'
define("port", default=8686, help="run on the given port", type=int)
define("run_job_file", default=PST_SRC+'/etc/autorun_conf.yaml',
       help="specify run jos file", type=str)


class TaskManager(object):
    def __init__(self, test_env):
        self.ioloop = tornado.ioloop
        self.test_env = test_env
        self.int_runtime = int(test_env.int_runtime)
        self.executor = futures.ThreadPoolExecutor(max_workers=MAX_WORKERS)

    def _on_run_one_job(self, source, data):
        data = data.decode().strip()
        job = source[1]
        if 'out' in source[0]:
            logging.info('Run Job Success : %s' % data)
            job.status = 'finished'

        if 'err' in source[0]:
            logging.error('Run Job FAILED : %s' % data)
            job.status = 'failed'

    def run_one_job(self, job):
        job.status = 'running'
        run_cmd = [PST_SRC+'/bin/pst', 'run', '-j', job.job_file,
                   '-u', self.test_env.upload_url]
        logging.info("(run_one_job: %s)" % run_cmd)
        try:
            job.start_time = time.strftime(TIMEFORMAT, time.localtime())
            common.run_cmd(run_cmd)
            job.status = 'finished'
        except Exception:
            job.status = 'failed'

    @run_on_executor
    def per_func(self):
        while True:
            time.sleep(self.int_runtime)
            for testjob in self.test_env.runjobs:
                logging.info("%s====" % testjob)
                self.run_one_job(testjob)
            self.test_env.reload()

    @gen.coroutine
    def start(self):
        yield self.per_func()


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r'/', MainHandler),
        ]
        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), 'templates'),
            static_path=os.path.join(os.path.dirname(__file__), 'static'),
            debug=True,)
        self.test_env = TestEnv(options.run_job_file)
        super(Application, self).__init__(handlers, **settings)


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        test_env = self.application.test_env
        self.render(
            'index.html',
            page_title="Pstbox | Home",
            header_text="All running testcase",
            test_env=test_env
        )

_default_testenv = None


def main():
    global _default_testenv
    tornado.options.parse_command_line()
    app = Application()
    _default_testenv = app.test_env
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(options.port)

    tornado.ioloop.IOLoop.current().add_callback(
        lambda: (TaskManager(_default_testenv).start()))
    tornado.ioloop.IOLoop.current().start()

if __name__ == "__main__":
    import pstbox.manlog
    logger = pstbox.manlog.logger
    main()
