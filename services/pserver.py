#!/usr/bin/env python

import os
import json
import tornado.httpserver
import tornado.ioloop
import tornado.options
from tornado.options import define, options
from tornado_json.application import Application
from tornado_json.routes import get_routes

from pst import common
from pst import influxdb_pst
from pst import secrets
from pservers import handlers
from pservers import modules

PST_SRC = os.getenv('PST_SRC', common.PST_SRC)

# load server config
conf_dict = common.load_yaml(PST_SRC + '/etc/pst_server.yaml')
server_port = str(conf_dict['pst_server']['port'])
print "=============server port: %s" % server_port

INFLUXDB_HOST = str(conf_dict['influxdb']['ip'])
INFLUXDB_PORT = str(conf_dict['influxdb']['port'])
INFLUXDB_USER = str(conf_dict['influxdb']['user'])
INFLUXDB_PASS = str(conf_dict['influxdb']['pass'])
INFLUXDB_DBNAME = str(conf_dict['influxdb']['dbname'])

define("port", default=server_port, help="run on the given port", type=int)

DIFF_SUB_TEST = ['sysbench']


class PServerApp(Application):
    def __init__(self, api_routes, db_conn=None, generate_docs=False):
        routes = [
                (r"/", handlers.IndexHandler),
                (r"/testboxes", handlers.TestBoxesHandler),
                (r"/login", handlers.LoginHandler),
                (r"/logout", handlers.LogoutHandler),
                (r"/results$", handlers.ResultsHandler),
                (r"/results/([\w-]+$)", handlers.ResultsHandler)
        ]
        routes += api_routes
        print("Routes\n========\n\n" + json.dumps(
            [(url, repr(rh)) for url, rh in routes],
            indent=2
        ))
        settings = dict(
                template_path=os.path.join(
                    os.path.dirname(__file__), "pservers/templates"),
                static_path=os.path.join(
                    os.path.dirname(__file__), "pservers/static"),
                ui_modules={
                    'Item': modules.ItemModule,
                    'PicContent': modules.PicContentModule,
                    'Pic': modules.PicModule,
                },
                cookie_secret='AG3oA/P0THOoHbRweDqx1mSGVsh3NULNqwfeFsxNQHg=',
                login_url='/login',
                debug=True,
        )
        self.influxdb_client = influxdb_pst.conn(INFLUXDB_HOST, INFLUXDB_PORT, INFLUXDB_USER, INFLUXDB_PASS, INFLUXDB_DBNAME)
        influxdb_pst.create_db(self.influxdb_client, INFLUXDB_DBNAME)
        self.prikey_path = '%s/pst_ssh_prikey' % PST_SRC
        self.pubkey_path = '%s/pst_ssh_pubkey' % PST_SRC
        if not os.path.exists(self.prikey_path) or not os.path.exists(self.pubkey_path):
            secrets.gen_ssh_keypair(self.prikey_path, self.pubkey_path)
        self.prikey_content = open(self.prikey_path, 'r').read()
        self.pubkey_content = open(self.pubkey_path, 'r').read()
        super(PServerApp, self).__init__(routes, settings, db_conn, generate_docs)


def main():
    os.environ['PST_MAIL_SUBJECT'] = u"[PST Server][log]"
    import pservers
    from motorengine import connect
    import pst.manlog

    logger = pst.manlog.logger
    logger.info("Starting PServer....")

    io_loop = tornado.ioloop.IOLoop.instance()
    connect('pst', io_loop=io_loop)
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(PServerApp(get_routes(pservers)))
    http_server.listen(options.port)
    io_loop.start()

if __name__ == "__main__":
    main()
