from tornado.escape import xhtml_escape
from tornado_json.requesthandlers import APIHandler
from tornado_json.gen import coroutine

from pservers.models import TestBox
from pservers.models import User


class TestBoxesAPIHandler(APIHandler):
    __url_names__ = ["testboxes"]

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
        import datetime
        hostname = xhtml_escape(self.get_argument('hostname'))
        password = xhtml_escape(self.get_argument('password'))

        testboxes = yield TestBox.objects.limit(1).filter(
            hostname=hostname,
            password=password
        ).find_all()
        if testboxes:
            testboxes[0].hostname = hostname
            testboxes[0].password = password
            testboxes[0].updated_at = datetime.datetime.now()
            tbox = testboxes[0]
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


class TestBoxesIdHandler(TestBoxesAPIHandler):

    @coroutine
    def get(self, boxid):
        try:
            boxid = self.current_user
        except KeyError:
            self.fail("No data on such make `{}`.".format(boxid))
