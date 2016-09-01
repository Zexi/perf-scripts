from tornado.escape import json_decode
from tornado_json import schema
from tornado_json.requesthandlers import APIHandler
from tornado_json.gen import coroutine

from pservers.models import TestBox


class TestBoxsAPIHandler(APIHandler):
    __url_names__ = ["testboxs"]


class TestBoxsListHandler(TestBoxsAPIHandler):

    @coroutine
    def get(self):
        testboxs = yield TestBox.objects.filter().find_all()
        self.success(testboxs[1])

    @coroutine
    def post(self):
        """
        POST the required parameters to post a TestBox env

        * `box_id`
        * `hostname`
        """
        body = json_decode(self.request.body)
        hostname = body['hostname']
        status = body['status']

        res = yield TestBox(
            hostname=hostname,
            status=status
        ).save()
        print(res)
        self.success(res.to_son())

class TestBoxsMakeListHandler(TestBoxsAPIHandler):

    @coroutine
    def get(self, make):
        try:
            self.success(DATA[make])
        except KeyError:
            self.fail("No data on such make `{}`.".format(make))
