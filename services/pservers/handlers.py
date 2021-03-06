import os
import shutil
import logging
import tornado.web
from tornado.gen import coroutine
from tornado.web import traceback
from tornado.concurrent import run_on_executor, futures

from pst import common
from pst import result
from pservers.models import User

logger = logging.getLogger(__name__)

MAX_WORKERS = 4
PST_SRC = os.getenv('PST_SRC', common.PST_SRC)
WORKSPACE = PST_SRC + '/workspace'


class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("username")

    def write_error(self, status_code, **kwargs):
        self.set_status(status_code)
        if self.settings.get("serve_traceback") and "exc_info" in kwargs:
            # in debug mode, try to send a traceback
            self.set_header('Content-Type', 'text/plain')
            for line in traceback.format_exception(*kwargs["exc_info"]):
                self.write(line)
            self.finish()
        else:
            if 404 == status_code:
                self.render('404.html')
            else:
                self.finish("<html><title>%(code)d: %(message)s</title>"
                            "<body>%(code)d: %(message)s</body></html>" % {
                                "code": status_code,
                                "message": self._reason,
                            })


class LoginHandler(BaseHandler):
    @coroutine
    def get(self):
        incorrect = self.get_secure_cookie("incorrect")
        if incorrect and int(incorrect) > 20:
            self.write('<center>blocked</center>')
            return
        self.render('login.html')

    @coroutine
    def post(self):
        incorrect = self.get_secure_cookie('incorrect')
        if incorrect and int(incorrect) > 20:
            self.write('<center>blocked</center>')
            return

        username = tornado.escape.xhtml_escape(self.get_argument('username'))
        password = tornado.escape.xhtml_escape(self.get_argument('password'))
        users = yield User.objects.limit(1).filter(name=username, password=password).find_all()
        if not users or not users[0].is_admin:
            self.set_status(401)
            incorrect = self.get_secure_cookie("incorrect") or 0
            increased = str(int(incorrect)+1)
            self.set_secure_cookie("incorrect", increased, httponly=True)
            self.write('''<center>
                            Something Wrong With Your Data (%s)<br />
                            <a href="/">Go Home</a>
                          </center> ''' % increased)

        else:
            self.set_secure_cookie("username", self.get_argument("username"), httponly=True)
            self.set_secure_cookie("Authorization", users[0].token)
            self.set_secure_cookie("incorrect", "0", httponly=True)
            self.redirect('/')


class LogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie("username")
        self.redirect(self.get_argument("next", "/"))


class IndexHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render('index.html', user=self.current_user)


class TestBoxesHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render('testbox.html')


class TestJobsHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render('testjob.html')


class ResultsHandler(BaseHandler):
    executor = futures.ThreadPoolExecutor(max_workers=MAX_WORKERS)

    @coroutine
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
            try:
                result.update_influxdb(
                    testcase, start_time, result_path,
                    influxdb_client, influxdb_tags)
                shutil.rmtree(result_path)
            except Exception:
                tb = traceback.format_exc()
                err_str = '%s\n%s' % (influxdb_tags, tb)
                logger.error(err_str)
                self.write_error(400)
