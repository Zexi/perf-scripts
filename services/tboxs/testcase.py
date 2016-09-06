import os
import logging
import requests
import json

from pst import common

PST_SRC = os.getenv('PST_SRC', common.PST_SRC)
CYCLIC_PATH = PST_SRC + '/workspace/cyclic-jobs'
TMP_PATH = PST_SRC + '/workspace/tmp'
logger = logging.getLogger(__name__)


class TestJob(object):
    def __init__(self, job_file_list,
                 pst_server='127.0.0.1', pst_server_port=18686,
                 testbox=common.get_hostname(),
                 password=None, token=None,
                 boxid=None, status='init'):
        self.origin_job_file = job_file_list[0]
        self.job_file = job_file_list[1]
        self.pserver_url = 'http://%s:%s' % (pst_server, pst_server_port)
        self.origin_desc = dict()
        self.desc = dict()
        self._load_job_file()
        self.testbox = testbox
        self.password = password
        self.token = token
        self.boxid = boxid
        self.status = status
        self.upload_info()

    def _load_job_file(self):
        logger.info('======TestJob origin load %s' % self.origin_job_file)
        self.origin_desc.update(common.load_yaml(self.origin_job_file))
        logger.info('======TestJob load %s' % self.job_file)
        self.desc.update(common.load_yaml(self.job_file))
        self.testcase = self.desc.get('testcase', None)
        self.job_params = self.desc.get('job_params', None)
        self.unit_job = self.desc.get('unit_job', None)
        self.commit = self.desc.get('commit', common.get_commit())
        self.rootfs = self.desc.get('rootfs', common.get_rootfs())

    def upload_info(self):
        api_url = '%s/api/testjobs' % (self.pserver_url)
        json_data = self.__str__()
        response = requests.post(api_url, data=json_data, headers={'Authorization': self.token})
        response.raise_for_status()

    def save_origin_job(self):
        common.save_yaml(self.origin_job_file, self.origin_desc)

    def __str__(self):
        return common.to_json(self.__dict__)

    __repr__ = __str__


class TestEnv(object):
    def __init__(self, run_job_file):
        self._load_runjobs(run_job_file)
        self._get_boxid()

    def _get_boxid(self):
        param = {'hostname': self.testbox, 'password': self.password}
        self.pserver_url = 'http://%s:%s/api/testboxes' % (self.pst_server, self.pst_server_port)
        response = requests.post(self.pserver_url, data=param, headers={'Authorization': self.token})
        response.raise_for_status()
        self.boxid = json.loads(response.content)['data']['box_id']

    def _load_runjobs(self, file_path):
        self.conf_file = file_path
        self.pst_src = PST_SRC
        self.runjobs_conf = common.load_yaml(file_path)
        self.pst_server = self.runjobs_conf.get('server').get('hostname')
        self.pst_server_port = self.runjobs_conf.get('server').get('port')
        self.pst_server_res = self.runjobs_conf.get('server').get('res')
        self.testbox = common.get_hostname()
        self.password = self.runjobs_conf.get('password', '')
        self.token = self.runjobs_conf.get('token', '')
        self.int_runtime = self.runjobs_conf.get('runtime')
        self.runjobs_sync_dir = self.runjobs_conf.get('sync').get('dir')

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
        data = common.run_cmd(split_cmd)
        logger.info('Split Job Success : %s' % data)
        split_jobs = [split_file.split(' => ') for split_file
                      in data.split('\n') if split_file]
        kvargs = {'testbox': self.testbox, 'password': self.password,
                  'pst_server': self.pst_server,
                  'pst_server_port': self.pst_server_port,
                  'token': self.token, 'boxid': self.boxid,
                  'status': 'splited'}
        self.runjobs = [TestJob(job_file_list, **kvargs) for job_file_list in split_jobs]

    def reload(self):
        print("=====================TestEnv relaod===============")
        self._load_runjobs(self.conf_file)
        # generate self.runjobs
        self._gen_testjobs(self.runjobs_conf.get('jobs', []))

    @property
    def upload_url(self):
        self._upload_url = 'http://%s:%s/%s' % \
                (self.pst_server, self.pst_server_port, self.pst_server_res)
        return self._upload_url

    @upload_url.setter
    def upload_url(self, hostname, port, res):
        self._upload_url = 'http://%s:%s/%s' % (hostname, port, res)

    def upload_job_status(self):
        pass
