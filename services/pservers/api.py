import json
import logging
from datetime import datetime
from tornado.escape import xhtml_escape
from tornado import gen
from tornado_json.requesthandlers import APIHandler
from tornado_json.gen import coroutine

from pservers.models import TestBox
from pservers.models import TestJob
from pservers.models import User
from pservers.ansible_pst import AnsibleTask
from pservers.ansible_pst import OPTIONS

logger = logging.getLogger(__name__)

class BaseAPIHandler(APIHandler):
    @coroutine
    def authenticated(self):
        key = self.get_secure_cookie('Authorization')
        if not key:
            key = self.request.headers.get('Authorization', None)
        if not key:
            self.set_status(403)
            self.fail('Forbidden')
            return
        users = yield User.objects.limit(1).filter(token=key).find_all()
        if not users or not users[0].is_admin:
            self.set_status(401)
            self.fail('Unauthorized')

    @coroutine
    def prepare(self):
        yield self.authenticated()
        self.ansible_options = OPTIONS(
            listtags=False, listtasks=False, listhosts=False,
            syntax=False, connection='ssh', module_path='',
            forks=100, remote_user='root',
            private_key_file=self.application.prikey_path,
            ssh_common_args=None, ssh_extra_args=None,
            sftp_extra_args=None, scp_extra_args=None,
            become=False, become_method=None,
            become_user='root', verbosity=None, check=False
        )

    @coroutine
    def testbox_find(self, **search_dict):
        testboxes = yield TestBox.objects.limit(1).filter(
            **search_dict
        ).find_all()

        if not testboxes:
            raise ValueError('Not found testbox: %s' % search_dict)
        raise gen.Return(testboxes[0])

    @coroutine
    def testjob_find(self, **search_dict):
        jobs = yield TestJob.objects.limit(1).filter(
            **search_dict
        ).find_all()

        if not jobs:
            raise ValueError('Not found testjob: %s' % search_dict)
        raise gen.Return(jobs[0])


class TestBoxesAPIHandler(BaseAPIHandler):
    __url_names__ = ["testboxes"]


class TestBoxesHandler(TestBoxesAPIHandler):
    @coroutine
    def get(self):
        testboxes = yield TestBox.objects.filter().find_all()
        testboxes = [testbox.to_son() for testbox in testboxes]
        self.success(testboxes)

    @coroutine
    def post(self):
        """
        POST the required parameters to register a TestBox env

        * `hostname`
        """
        hostname = xhtml_escape(self.get_argument('hostname'))
        password = xhtml_escape(self.get_argument('password'))
        box_ip = self.request.remote_ip

        try:
            testbox = yield self.testbox_find(
                hostname=hostname,
                password=password
            )
            testbox.hostname = hostname
            testbox.password = password
            testbox.box_ip = box_ip
            testbox.pubkey = self.application.pubkey_content
            testbox.updated_at = datetime.now()
        except ValueError:
            testbox = TestBox(
                hostname=hostname,
                password=password,
                box_ip=box_ip,
                pubkey=self.application.pubkey_content,
                created_at=datetime.now()
            )
        res = yield testbox.save()
        print(res)
        self.set_status(201)
        self.success(res.to_son())


class TestBoxesIdHandler(TestBoxesAPIHandler):
    @coroutine
    def get(self, boxid):
        try:
            testbox = yield self.testbox_find(box_id=boxid)
            self.success(testbox.to_son())
        except ValueError as e:
            self.fail("No data on such make `{}`.".format(e))


class TestJobsAPIHandler(BaseAPIHandler):
    __url_names__ = ["testjobs"]


class TestJobsHandler(TestJobsAPIHandler):
    @coroutine
    def get(self):
        testjobs = yield TestJob.objects.filter().find_all()
        testjobs = [testjob.to_son() for testjob in testjobs]
        self.success(testjobs)

    @coroutine
    def post(self):
        json_data = self.request.body
        hash_data = json.loads(json_data)
        boxid = hash_data['boxid']
        testcase = hash_data['testcase']
        job_params = hash_data['job_params']
        testbox = hash_data['testbox']
        rootfs = hash_data['rootfs']
        commit = hash_data['commit']
        origin_desc = hash_data['origin_desc']
        desc = hash_data['desc']
        status = hash_data['status']

        try:
            job = yield self.testjob_find(
                boxid=boxid, testcase=testcase,
                testbox=testbox, rootfs=rootfs,
                commit=commit, job_params=job_params
            )
            job.status = status
            job.updated_at = datetime.now()
        except ValueError:
            job = TestJob(
                boxid=boxid, testcase=testcase,
                testbox=testbox, rootfs=rootfs,
                commit=commit, job_params=job_params,
                origin_desc=origin_desc, desc=desc,
                status=status,
                created_at=datetime.now()
            )
        res = yield job.save()
        print(res)
        self.set_status(201)
        self.success(res.to_son())


class TestJobsIdHandler(TestJobsAPIHandler):
    @coroutine
    def get(self, jobid):
        try:
            testjob = yield self.testjob_find(job_id=jobid)
            self.success(testjob.to_son())

        except ValueError:
            self.fail("No data on such make `{}`.".format(jobid))

    @coroutine
    def post(self, jobid):
        pass


class TestJobsAnsibleHandler(TestJobsHandler):
    __url_names__ = []
    __urls__ = [r"/api/testjobs/(?P<jobid>[a-zA-Z0-9_\-]+)/details/?$"]

    @coroutine
    def get(self, jobid):
        try:
            job = yield self.testjob_find(job_id=jobid)
            testbox = yield self.testbox_find(box_id=job.boxid)
            remote_ip = testbox.box_ip
            module = 'uri'
            uri_args = dict(
                url='http://localhost:8686/api/jjobs/%s' % jobid,
                method='GET', return_content='yes'
            )
            uri_task = AnsibleTask(
                remote_ip, module, args=uri_args,
                options=self.ansible_options
            )
            result = uri_task.ansible_play()
            self.success(result)
        except ValueError as e:
            logger.warning("No data on such make `{}`.".format(e))
            self.fail("No data on such make `{}`.".format(e))
