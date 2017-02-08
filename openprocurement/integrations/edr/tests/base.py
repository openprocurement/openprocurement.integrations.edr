from gevent import monkey; monkey.patch_all()
from gevent.pywsgi import WSGIServer
import os
import webtest
from bottle import Bottle
from openprocurement.integrations.edr.tests._server import setup_routing
from openprocurement.api.tests.base import (
    BaseWebTest as _BaseWebTest,
    PrefixedRequestClass)


class BaseWebTest(_BaseWebTest):

    """Base Web Test to test openprocurement.integrations.edr. """

    relative_to = os.path.dirname(__file__)  # crafty line

    @classmethod
    def setUpClass(cls):
        cls.edr_api_app = Bottle()
        setup_routing(cls.edr_api_app)
        from paste.deploy.loadwsgi import appconfig
        config = appconfig('config:tests.ini', "main", relative_to=cls.relative_to)
        cls.server = WSGIServer(('localhost', 20603), cls.edr_api_app, log=None)
        cls.server.start()
        for _ in range(10):
            try:
                cls.app = webtest.TestApp("config:tests.ini",
                                          relative_to=cls.relative_to)
            except:
                pass
            else:
                break
        else:
            cls.app = webtest.TestApp("config:tests.ini",
                                      relative_to=cls.relative_to)
        cls.app.RequestClass = PrefixedRequestClass

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        self.app.authorization = ('Basic', ('token', ''))
        # self.app.authorization = ('Basic', ('broker', ''))

    def tearDown(self):
        pass
