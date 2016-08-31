#!/usr/bin/env python

import os
import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.options
from tornado.options import define, options

from pst import common
from pst import result
from pst import influxdb_pst

PST_SRC = os.getenv('PST_SRC', common.PST_SRC)
WORKSPACE = PST_SRC + '/workspace'

# load server config
conf_dict = common.load_yaml(PST_SRC + '/etc/pst_server.yaml')
server_port = str(conf_dict['pst_server']['port'])

INFLUXDB_HOST = str(conf_dict['influxdb']['ip'])
INFLUXDB_PORT = str(conf_dict['influxdb']['port'])
INFLUXDB_USER = str(conf_dict['influxdb']['user'])
INFLUXDB_PASS = str(conf_dict['influxdb']['pass'])
INFLUXDB_DBNAME = str(conf_dict['influxdb']['dbname'])

define("port", default=server_port, help="run on the given port", type=int)

DIFF_SUB_TEST = ['sysbench']


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
                (r"/", IndexHandler),
                (r"/results$", ResultsHandler),
                (r"/results/([\w-]+$)", ResultsHandler)
        ]
        settings = dict(
                template_path=os.path.join(
                    os.path.dirname(__file__), "templates"),
                static_path=os.path.join(
                    os.path.dirname(__file__), "static"),
                ui_modules={
                    'Item': ItemModule,
                    'PicContent': PicContentModule,
                    'Pic': PicModule,
                },
                debug=True,)
        self.influxdb_client = influxdb_pst.conn(INFLUXDB_HOST, INFLUXDB_PORT, INFLUXDB_USER, INFLUXDB_PASS, INFLUXDB_DBNAME)
        influxdb_pst.create_db(self.influxdb_client, INFLUXDB_DBNAME)
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

        influxdb_client = self.application.influxdb_client

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
            testcase_prefix = '%s/%s/%s/%s/%s' % (
                testcase, job_params, testbox, rootfs, commit)

            influxdb_tags = {
                'testcase': testcase,
                'job_params': job_params,
                'testbox': testbox,
                'rootfs': rootfs,
                'commit': commit,
            }

            result_path = '%s/results/%s/%s' % (
                WORKSPACE, testcase_prefix, start_time)
            result.update_influxdb(
                testcase, start_time, result_path,
                influxdb_client, influxdb_tags)


def main():
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    os.environ['PST_MAIL_SUBJECT'] = u"[PST Server][log]"
    import pst.manlog
    logger = pst.manlog.logger
    main()
