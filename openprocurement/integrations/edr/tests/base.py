import unittest
import os
import webtest
import subprocess
import time
from redis import StrictRedis
from gevent import monkey; monkey.patch_all()
from gevent.pywsgi import WSGIServer
from bottle import Bottle
from openprocurement.integrations.edr.utils import ROUTE_PREFIX


class PrefixedRequestClass(webtest.app.TestRequest):

    @classmethod
    def blank(cls, path, *args, **kwargs):
        path = '{0}{1}'.format(ROUTE_PREFIX, path)
        return webtest.app.TestRequest.blank(path, *args, **kwargs)


class BaseWebTest(unittest.TestCase):

    """Base Web Test to test openprocurement.integrations.edr. """

    relative_to = os.path.dirname(__file__)  # crafty line
    redis = None
    redis_process = None
    PORT = 16379

    @classmethod
    def setUpClass(cls):
        cls.edr_api_app = Bottle()
        cls.server = WSGIServer(('localhost', 20603), cls.edr_api_app, log=None)
        cls.server.start()
        for _ in range(10):
            try:
                cls.app = webtest.TestApp("config:tests.ini", relative_to=cls.relative_to)
            except:
                pass
            else:
                break
        else:
            cls.app = webtest.TestApp("config:tests.ini", relative_to=cls.relative_to)
        cls.app.RequestClass = PrefixedRequestClass
        cls.redis_process = subprocess.Popen(['redis-server', '--port', str(cls.PORT)])
        time.sleep(0.1)
        cls.redis = StrictRedis(port=cls.PORT)

    @classmethod
    def tearDownClass(cls):
        cls.server.close()
        cls.redis_process.terminate()
        cls.redis_process.wait()

    def tearDown(self):
        self.redis.flushall()

    def setUp(self):
        self.app.authorization = ('Basic', ('platform', 'platform'))
