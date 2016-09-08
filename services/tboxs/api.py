from tornado_json.requesthandlers import APIHandler
from tornado_json.gen import coroutine


class BaseAPIHandler(APIHandler):
    @coroutine
    def prepare(self):
        pass


class JobsAPIHandler(BaseAPIHandler):
    __url_names__ = ["jobs"]


class JobsHandler(JobsAPIHandler):
    @coroutine
    def get(self):
        test_env_list = self.application.test_env_list
        jobs = [job.to_json() for test_env in test_env_list
                for job in test_env.runjobs]
        self.success(jobs)


class JobsIdHandler(JobsAPIHandler):
    @coroutine
    def get(self, jobid):
        job = None
        for test_env in self.application.test_env_list:
            job = test_env.find_job(jobid)
        if job:
            self.success(job.__dict__)
        else:
            self.fail('Not found job: %s' % jobid)
