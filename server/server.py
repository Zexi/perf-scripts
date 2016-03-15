#!/usr/bin/env python2.7

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
LIB_PATH = SRC + '/lib'
sys.path.insert(0, LIB_PATH)
import common
import mongodb

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
                (r"/", IndexHandler),
                (r"/results$", ResultsHandler),
                (r"/results/([\w]+$)", ResultsHandler)
                #(r"/stats/([\w-\d]+)/(plot)$", ResultsHandler, dict(common_string='Value defined in Application')),
        ]
        mongo_conn = mongodb.client("localhost", 27017)
        self.results_db = mongo_conn["results"]
#        self.rootfs_commit_db = mongo_conn["rootfs_commit"]
#        self.testbox_db = mongo_conn["testbox"]
#        self.unitjob_db = mongo_conn["unitjob"]

        tornado.web.Application.__init__(self, handlers, debug=True)

class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        greeting = self.get_argument('greeting', 'Hello')
        self.write(greeting + ', friendly user!')

class PlotHandler(tornado.web.RequestHandler):
    def initialize(self, common_string):
        self.common_string = common_string

    def get(self, plot_id):
        response = { 'plot': plot_id,
                     'name':'Plot test results',
                     'common_string': self.common_string
                     }
        self.write(response)

class ResultsHandler(tornado.web.RequestHandler):
    def get(self, result_name=None):
        if result_name:
            self.write(result_name)
        else:
            results_coll = self.application.results_db.results
            doc_list = mongodb.coll_findall(results_coll)
            for doc in doc_list: 
                del doc["_id"]
                self.write(common.to_json(doc))

    def post(self):
        files = self.request.files
        testbox = self.get_argument("testbox")
        rootfs = self.get_argument("rootfs")
        commit = self.get_argument("commit")
        unit_job = self.get_argument("unit_job")
        start_time = self.get_argument("start_time")
        testcase = self.get_argument("testcase")
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
        results_coll = self.application.results_db.results
        #testboxs_coll = self.application.results_db.testboxs
        mongodb.coll_insert(results_coll, {"testbox": testbox, "rootfs": rootfs, "commit": commit, "unit_job": unit_job, "start_time": start_time, "testcase": testcase})
        #mongodb.coll_insert(testboxs_coll, {"testbox": testbox})

if __name__ == "__main__":
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()
