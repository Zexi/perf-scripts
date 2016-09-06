import json
from datetime import datetime
from tornado.escape import xhtml_escape
from tornado_json.requesthandlers import APIHandler
from tornado_json.gen import coroutine

from pservers.models import TestBox
from pservers.models import TestJob
from pservers.models import User


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

        testboxes = yield TestBox.objects.limit(1).filter(
            hostname=hostname,
            password=password
        ).find_all()
        if testboxes:
            testboxes[0].hostname = hostname
            testboxes[0].password = password
            testboxes[0].updated_at = datetime.now()
            tbox = testboxes[0]
        else:
            tbox = TestBox(
                hostname=hostname,
                password=password,
                created_at=datetime.now()
            )
        res = yield tbox.save()
        print(res)
        self.set_status(201)
        self.success(res.to_son())


class TestBoxesIdHandler(TestBoxesAPIHandler):
    @coroutine
    def get(self, boxid):
        try:
            boxid = self.current_user
        except KeyError:
            self.fail("No data on such make `{}`.".format(boxid))


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

        jobs = yield TestJob.objects.limit(1).filter(
            boxid=boxid, testcase=testcase,
            testbox=testbox, rootfs=rootfs,
            commit=commit, job_params=job_params,
        ).find_all()
        if jobs:
            jobs[0].status = status
            jobs[0].updated_at = datetime.now()
            job = jobs[0]
        else:
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
