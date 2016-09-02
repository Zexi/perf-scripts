from tornado.escape import xhtml_escape
from tornado.escape import json_decode
from tornado_json import schema
from tornado_json.requesthandlers import APIHandler
from tornado_json.gen import coroutine

from pservers.models import TestBox
from pservers.models import User


class TestBoxsAPIHandler(APIHandler):
    __url_names__ = ["testboxs"]

    @coroutine
    def authenticated(self):
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


class TestBoxsListHandler(TestBoxsAPIHandler):
    @coroutine
    def get(self):
        testboxs = yield TestBox.objects.filter().find_all()
        self.success(testboxs[0].to_son())

    @coroutine
    def post(self):
        """
        POST the required parameters to register a TestBox env

        * `hostname`
        """
        import datetime
        hostname = xhtml_escape(self.get_argument('hostname'))
        password = xhtml_escape(self.get_argument('password'))

        testboxs = yield TestBox.objects.limit(1).filter(
            hostname=hostname,
            password=password
        ).find_all()
        if testboxs:
            testboxs[0].hostname = hostname
            testboxs[0].password = password
            testboxs[0].updated_at = datetime.datetime.now()
            tbox = testboxs[0]
        else:
            tbox = TestBox(
                hostname=hostname,
                password=password,
                created_at=datetime.datetime.now()
            )
        res = yield tbox.save()
        print(res)
        self.set_status(201)
        self.success(res.to_son())


class TestBoxsIdListHandler(TestBoxsAPIHandler):

    @coroutine
    def get(self, box_id):
        try:
            box_id = self.current_user
        except KeyError:
            self.fail("No data on such make `{}`.".format(box_id))
