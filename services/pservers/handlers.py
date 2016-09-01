import os
import tornado.web
from tornado import gen
from tornado.concurrent import run_on_executor, futures

from pst import common
from pst import result

MAX_WORKERS = 4
PST_SRC = os.getenv('PST_SRC', common.PST_SRC)
WORKSPACE = PST_SRC + '/workspace'

class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('index.html')


class ResultsHandler(tornado.web.RequestHandler):
    executor = futures.ThreadPoolExecutor(max_workers=MAX_WORKERS)

    def get(self, testcase_name=None):
        if testcase_name:
            pass
        else:
            pass

    @gen.coroutine
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
