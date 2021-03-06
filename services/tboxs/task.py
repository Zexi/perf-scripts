import os
import time
import logging
from tornado.ioloop import IOLoop
from tornado import gen
from tornado.concurrent import run_on_executor, futures

from pst import common

MAX_WORKERS = 4
TIMEFORMAT = '%Y-%m-%d-%X'
PST_SRC = os.getenv('PST_SRC', common.PST_SRC)

logger = logging.getLogger(__name__)


class TaskRunner(object):
    def __init__(self, test_env):
        self.ioloop = IOLoop.current()
        self.test_env = test_env
        self.int_runtime = int(test_env.int_runtime)
        self.executor = futures.ThreadPoolExecutor(max_workers=MAX_WORKERS)

    def _on_run_one_job(self, source, data):
        data = data.decode().strip()
        job = source[1]
        if 'out' in source[0]:
            logger.info('Run Job Success : %s' % data)
            job.status = 'finished'

        if 'err' in source[0]:
            logger.error('Run Job FAILED : %s' % data)
            job.status = 'failed'

    def run_one_job(self, job):
        upload_url = self.test_env.upload_url
        job.status = 'running'
        job.upload_info()
        run_cmd = [PST_SRC+'/bin/pst', 'run', '-j', job.job_file,
                   '-u', upload_url]
        cleanup_cmd = [PST_SRC+'/sbin/cleanup', '-d', '1', '/results']
        logger.info("(run_one_job: %s)" % run_cmd)
        try:
            common.run_cmd(cleanup_cmd)
            job.start_time = time.strftime(TIMEFORMAT, time.localtime())
            common.run_cmd(run_cmd)
            job.status = 'finished'
            job.upload_info()
            logger.info("Finish run_one_job: %s, remove it" % job.job_file)
            os.remove(job.job_file)
        except Exception:
            job.status = 'failed'
            job.upload_info()

    def reload_sleep(self):
        self.int_runtime = int(self.test_env.int_runtime)
        try:
            self.test_env.reload()
        except Exception as e:
            logger.error('Reload sleep error: %s' % e)
        finally:
            time.sleep(self.int_runtime)

    @run_on_executor
    def per_func(self):
        while True:
            self.reload_sleep()
            for testjob in self.test_env.runjobs:
                logger.info("%s====" % testjob)
                try:
                    self.run_one_job(testjob)
                except Exception as e:
                    logger.error('run one job error: %s' % e)

    @gen.coroutine
    def start(self):
        yield self.per_func()


class TaskManager(object):
    def __init__(self, test_env_list):
        self.ioloop = IOLoop.current()
        self.test_env_list = test_env_list

    def start(self):
        for test_env in self.test_env_list:
            self.ioloop.add_callback(
                lambda test_env=test_env: (TaskRunner(test_env).start())
            )
