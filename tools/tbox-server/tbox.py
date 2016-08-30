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

from tornado.process import Subprocess
from tornado.iostream import PipeIOStream
from tornado import gen
from tornado.options import define, options
from tornado.concurrent import run_on_executor, futures

from pstbox import common

MAX_WORKERS = 4
PST_SRC = os.getenv('PST_SRC', common.parent_dir(os.path.abspath(__file__), 2))
CYCLIC_PATH = PST_SRC + '/workspace/cyclic-jobs'
TMP_PATH = PST_SRC + '/workspace/tmp'
TIMEFORMAT = '%Y-%m-%d-%X'
define("port", default=8686, help="run on the given port", type=int)
define("run_job_file", default=PST_SRC+'/etc/autorun_conf.yaml',
       help="specify run jos file", type=str)


class AASubprocess(Subprocess):
    """
    Extension to tornado.process.Subprocess to support
    - process timeout
    - pass stdin bytes
    - real-time stdout data chunk callback
    - real-time stderr data chunk callback
    - process end callback
    """
    def __init__(
                self,
                command,
                timeout=-1,
                stdout_chunk_callback=None,
                stderr_chunk_callback=None,
                exit_process_callback=None,
                stdin_bytes=None,
                io_loop=None,
                kill_on_timeout=False
                ):
        """
        Initializes the subprocess with callbacks and timeout.

        :param command: command like ['java', '-jar', 'test.jar']
        :param timeout: timeout for subprocess to complete, if negative or \
        zero then no timeout
        :param stdout_chunk_callback: callback(bytes_data_chuck_from_stdout)
        :param stderr_chunk_callback: callback(bytes_data_chuck_from_stderr)
        :param exit_process_callback: callback(exit_code, \
        was_expired_by_timeout)
        :param stdin_bytes: bytes data to send to stdin
        :param io_loop: tornado io loop on None for current
        :param kill_on_timeout: kill(-9) or terminate(-15)?
        """
        self.aa_exit_process_callback = exit_process_callback
        self.aa_kill_on_timeout = kill_on_timeout
        stdin = Subprocess.STREAM if stdin_bytes else None
        stdout = Subprocess.STREAM if stdout_chunk_callback else None
        stderr = Subprocess.STREAM if stderr_chunk_callback else None

        Subprocess.__init__(self, command, stdin=stdin, stdout=stdout,
                            stderr=stderr, io_loop=io_loop)

        self.aa_process_expired = False
        self.aa_terminate_timeout = self.io_loop.call_later(
            timeout, self.aa_timeout_callback) if timeout > 0 else None

        self.set_exit_callback(self.aa_exit_callback)

        if stdin:
            self.stdin.write(stdin_bytes)
            self.stdin.close()

        if stdout:
            output_stream = PipeIOStream(self.stdout.fileno())

            def on_stdout_chunk(data):
                stdout_chunk_callback(data)
                if not output_stream.closed():
                    output_stream.read_bytes(102400,
                                             on_stdout_chunk, None, True)

            output_stream.read_bytes(102400, on_stdout_chunk, None, True)

        if stderr:
            stderr_stream = PipeIOStream(self.stderr.fileno())

            def on_stderr_chunk(data):
                stderr_chunk_callback(data)
                if not stderr_stream.closed():
                    stderr_stream.read_bytes(102400,
                                             on_stderr_chunk, None, True)

            stderr_stream.read_bytes(102400, on_stderr_chunk, None, True)

    def aa_timeout_callback(self):
        if self.aa_kill_on_timeout:
            self.proc.kill()
        else:
            self.proc.terminate()
        self.aa_process_expired = True

    def aa_exit_callback(self, status):
        if self.aa_terminate_timeout:
            self.io_loop.remove_timeout(self.aa_terminate_timeout)
        # need to post this call to make sure it is processed AFTER all outputs
        if self.aa_exit_process_callback:
            self.io_loop.add_callback(self.aa_exit_process_callback,
                                      status, self.aa_process_expired)


class TestJob(object):
    def __init__(self, job_file, status='init'):
        self.job_file = job_file
        self.desc = dict()
        self._load_job_file(job_file)
        self.status = status

    def _load_job_file(self, job_file):
        logging.info('======TestJob load %s' % job_file)
        self.desc.update(common.load_yaml(job_file))
        self.name = self.desc.get('testcase', None)
        self.job_params = self.desc.get('job_params', None)
        self.unit_job = self.desc.get('unit_job', None)
        self.testbox = self.desc.get('testbox', common.get_hostname())
        self.commit = self.desc.get('commit', common.get_commit())
        self.rootfs = self.desc.get('rootfs', common.get_rootfs())

    def __str__(self):
        return str(self.__dict__)

    __repr__ = __str__


class TestEnv(object):
    def __init__(self, run_job_file):
        self._load_runjobs(run_job_file)

    def _load_runjobs(self, file_path):
        self.conf_file = file_path
        self.pst_src = PST_SRC
        self.runjobs_conf = common.load_yaml(file_path)
        self.pst_server = self.runjobs_conf.get('server').get('hostname')
        self.pst_server_port = self.runjobs_conf.get('server').get('port')
        self.pst_server_res = self.runjobs_conf.get('server').get('res')
        self.int_runtime = self.runjobs_conf.get('runtime')
        self.runjobs_sync_dir = self.runjobs_conf.get('sync').get('dir')
        # generate self.runjobs
        self._gen_testjobs(self.runjobs_conf.get('jobs', []))

    def _on_gen_testjobs(self, source, data):
        data = data.decode().strip()
        if 'out' in source:
            logging.info('Split Job Success : %s' % data)
            split_jobs = [split_file.split(' => ')[1] for split_file
                          in data.split('\n') if split_file]
            self.runjobs = [TestJob(job_file, 'splited') for job_file
                            in split_jobs]
        if 'err' in source:
            logging.critical('Split Job FAILED : %s' % data)
            self.runjobs = None

    def _gen_testjobs(self, job_list):
        common.create_dir(self.pst_src)
        common.create_dir(TMP_PATH)
        common.create_dir(CYCLIC_PATH)
        cyclic_jobs = [self.pst_src + '/jobs/' + path + '.yaml'
                       for path in job_list]
        split_cmd = [self.pst_src+'/bin/pst', 'split', '-j']
        split_cmd = split_cmd + cyclic_jobs
        split_cmd.append("-o")
        split_cmd.append(CYCLIC_PATH)
        logging.info('(_gen_testjobs: %s)' % split_cmd)
#        AASubprocess(split_cmd, -1, partial(self._on_gen_testjobs, 'out'),
#                     partial(self._on_gen_testjobs, 'err'), None, None)

        data = common.run_cmd(split_cmd)
        logging.info('Split Job Success : %s' % data)
        split_jobs = [split_file.split(' => ')[1] for split_file
                      in data.split('\n') if split_file]
        self.runjobs = [TestJob(job_file, 'splited') for job_file
                        in split_jobs]

    def reload(self):
        print("=====================TestEnv relaod===============")
        self._load_runjobs(self.conf_file)

    @property
    def upload_url(self):
        self._upload_url = 'http://%s:%s/%s' % \
                (self.pst_server, self.pst_server_port, self.pst_server_res)
        return self._upload_url

    @upload_url.setter
    def upload_url(self, hostname, port, res):
        self._upload_url = 'http://%s:%s/%s' % (hostname, port, res)


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
