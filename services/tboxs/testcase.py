import os
import logging

from pst import common

PST_SRC = os.getenv('PST_SRC', common.PST_SRC)
CYCLIC_PATH = PST_SRC + '/workspace/cyclic-jobs'
TMP_PATH = PST_SRC + '/workspace/tmp'
logger = logging.getLogger(__name__)


class TestJob(object):
    def __init__(self, job_file, status='init'):
        self.job_file = job_file
        self.desc = dict()
        self._load_job_file(job_file)
        self.status = status

    def _load_job_file(self, job_file):
        logger.info('======TestJob load %s' % job_file)
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
            logger.info('Split Job Success : %s' % data)
            split_jobs = [split_file.split(' => ')[1] for split_file
                          in data.split('\n') if split_file]
            self.runjobs = [TestJob(job_file, 'splited') for job_file
                            in split_jobs]
        if 'err' in source:
            logger.critical('Split Job FAILED : %s' % data)
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
        logger.info('(_gen_testjobs: %s)' % split_cmd)
#        AASubprocess(split_cmd, -1, partial(self._on_gen_testjobs, 'out'),
#                     partial(self._on_gen_testjobs, 'err'), None, None)

        data = common.run_cmd(split_cmd)
        logger.info('Split Job Success : %s' % data)
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
