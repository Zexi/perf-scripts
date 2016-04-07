#!/usr/bin/env python

import os
import sys
import logging.config
import yaml
import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.options

from tornado.options import define, options
define("port", default=8080, help="run on the given port", type=int)

SRC = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))
WORKSPACE = SRC + '/workspace'
RRDB_PATH = WORKSPACE + '/rrdb'
LOG_PATH = WORKSPACE + '/logs'
LOG_FILE = LOG_PATH + '/server.log'
LIB_PATH = SRC + '/lib'
sys.path.insert(0, LIB_PATH)
import common
import mongodb
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
        conn = mongodb.client('localhost', 27017)
        self.db = conn["pst"]
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
            pass
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

        db_coll = self.application.db.results

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

            # record testcase info to mongodb
            mongodb.coll_insert(db_coll, {
                'testcase': testcase,
                'job_params': job_params,
                'testbox': testbox,
                'rootfs': rootfs,
                'commit': commit,
                'rrdb_file': rrdb_file,
                })

            if not os.path.exists(RRDB_PATH + '/' + testcase_prefix):
                os.makedirs(RRDB_PATH + '/' + testcase_prefix, 02775)
            result_path = '%s/results/%s/%s' % (WORKSPACE, testcase_prefix, start_time)
            if testcase in DIFF_SUB_TEST:
                result.update_rrdbs(str(testcase), rrdb_file, start_time, result_path, job_params)
                result.plot_rrdbs(db_coll, testcase_prefix, accord_param=True)
            else:
                result.update_rrdbs(str(testcase), rrdb_file, start_time, result_path)
                result.plot_rrdbs(db_coll, testcase_prefix)

def init_log():
    if not os.path.exists(LOG_PATH):
        os.makedirs(LOG_PATH, 02775)
    if not os.path.exists(LOG_FILE):
        os.system("touch %s" % LOG_FILE)

    dict_conf = yaml.load(open(SRC + '/etc/server_log.yaml', 'r'))
    dict_conf['handlers']['all']['filename'] = LOG_FILE
    logging.config.dictConfig(dict_conf)
    logging.info("Starting torando web server")

if __name__ == "__main__":
    tornado.options.parse_command_line()
    init_log()
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()
