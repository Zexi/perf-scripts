#!/usr/bin/env python

import os
import sys
import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.options

from tornado.options import define, options
define("port", default=8080, help="run on the given port", type=int)

SRC = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))
WORKSPACE = SRC + '/workspace'
RRDB_PATH = WORKSPACE + '/rrdb'
LIB_PATH = SRC + '/lib'
sys.path.insert(0, LIB_PATH)
import common
import result

DIFF_SUB_TEST = ['sysbench']

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
                (r"/", IndexHandler),
                (r"/results$", ResultsHandler),
                (r"/results/([\w-]+$)", ResultsHandler)
        ]
        settings = dict(
                template_path=os.path.join(os.path.dirname(__file__), "templates"),
                static_path=os.path.join(os.path.dirname(__file__), "static"),
                ui_modules={'Item': ItemModule, 'PicContent': PicContentModule, 'Pic': PicModule },
                debug=True
                )

        tornado.web.Application.__init__(self, handlers, **settings)

class ItemModule(tornado.web.UIModule):
    def render(self, item):
        return self.render_string('modules/item.html', item=item)

class PicContentModule(tornado.web.UIModule):
    def render(self, pics_dict):
        return self.render_string('modules/pic_content.html', pics_dict=pics_dict)

class PicModule(tornado.web.UIModule):
    def render(self, prefix, pics):
        return self.render_string('modules/pic.html', prefix=prefix, pics=pics)

class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('index.html', pics_dict=result.get_testcase_pic())

class ResultsHandler(tornado.web.RequestHandler):
    def get(self, testcase_name=None):
        if testcase_name:
            result.plot_rrdbs(testcase_name)
        else:
            pass

    def post(self):
        files = self.request.files
        testbox = self.get_argument("testbox")
        rootfs = self.get_argument("rootfs")
        commit = self.get_argument("commit")
        start_time = self.get_argument("start_time")
        testcase = self.get_argument("testcase")
        job_params = self.get_argument("job_params")

        upload_path = WORKSPACE + '/tmp'
        if not os.path.exists(upload_path):
            os.makedirs(upload_path, 02775)

        for k, v in files.iteritems():
            for file_meta in v:
                filename = file_meta['filename']
                filepath = os.path.join(upload_path, filename)
                with open(filepath, 'w') as up:
                    up.write(file_meta['body'])
                if 'tar.gz' in filepath:
                    common.extract_tar_gz(filepath, WORKSPACE)
                    os.remove(filepath)
            self.write('Upload %s successfully!\n' % filename)
            # rrdb_file will be unicode str, rrdtool not support it
            testcase_prefix = '%s/%s/%s/%s/%s' % (testcase, job_params, testbox, rootfs, commit)
            rrdb_file = str(RRDB_PATH + '/' + testcase_prefix + '/record.rrd')
            if not os.path.exists(RRDB_PATH + '/' + testcase_prefix):
                os.makedirs(RRDB_PATH + '/' + testcase_prefix, 02775)
            result_path = '%s/results/%s/%s' % (WORKSPACE, testcase_prefix, start_time)
            if testcase in DIFF_SUB_TEST:
                result.update_rrdbs(str(testcase), rrdb_file, start_time, result_path, job_params)
                result.plot_rrdbs(testcase_prefix, accord_param=True)
            else:
                result.update_rrdbs(str(testcase), rrdb_file, start_time, result_path)
                result.plot_rrdbs(testcase_prefix)

if __name__ == "__main__":
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()
