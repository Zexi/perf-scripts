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
    def post(self):
        files = self.request.files
        testbox = self.get_argument("testbox")
        rootfs = self.get_argument("rootfs")
        commit = self.get_argument("commit")
        unit_job = self.get_argument("unit_job")
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

if __name__ == "__main__":
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()
