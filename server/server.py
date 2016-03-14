import os
import sys
import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.options

import time
from tornado.options import define, options
define("port", default=8080, help="run on the given port", type=int)

SRC = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))
WORKSPACE = SRC + '/workspace'
TIMEFORMAT='%Y-%m-%d-%X'

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
                (r"/", IndexHandler),
                (r"/plot", PlotHandler),
                (r"/post", PostHandler)
        ]
        tornado.web.Application.__init__(self, handlers, debug=True)

class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        greeting = self.get_argument('greeting', 'Hello')
        self.write(greeting + ', friendly user!')


class PlotHandler(tornado.web.RequestHandler):
    def get(self, plot_id):
        self.write("You requested the plot" + plot_id)

class PostHandler(tornado.web.RequestHandler):
    def create_result_root(self, _result_root):
        now_time =  time.strftime(TIMEFORMAT, time.localtime())
        result_root = _result_root + os.sep + now_time
        os.makedirs(result_root, 02775)
        return result_root

    def post(self):
        files = self.request.files
        testbox = self.get_argument("testbox")
        rootfs = self.get_argument("rootfs")
        commit = self.get_argument("commit")
        unit_job = self.get_argument("unit_job")
        _upload_path = "%s/%s/%s-%s/%s" % (WORKSPACE, testbox, rootfs, commit, unit_job)
        upload_path = self.create_result_root(_upload_path.replace('"', ''))
        if not upload_path:
            sys.stderr.write("Can't create upload_path: %s" % upload_path)
            self.write("Can't create upload_path: %s" % upload_path)
            self.finish()


        for k, v in files.iteritems():
            for file_meta in v:
                filename = file_meta['filename']
                filepath = os.path.join(upload_path, filename)
                with open(filepath, 'w') as up:
                    up.write(file_meta['body'])
            self.write('Upload %s successfully!\n' % file)

if __name__ == "__main__":
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()
