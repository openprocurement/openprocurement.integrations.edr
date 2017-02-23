# -*- coding: utf-8 -*-
import json
import os
from datetime import datetime

import openprocurement.integrations.edr.tests.base as base_test

from openprocurement.integrations.edr.tests.base import BaseWebTest, PrefixedRequestClass
from openprocurement.integrations.edr.tests._server import setup_routing, response_code, response_passport
from webtest import TestApp

now = datetime.now()

edrpou = u"14360570"
ipn = u"1234567891"
passport = u"АБ123456"
invalid_passport = u"АБВ"
invalid_edrpou = u"123"


class DumpsTestAppwebtest(TestApp):
    def do_request(self, req, status=None, expect_errors=None):
        req.headers.environ["HTTP_HOST"] = "api-sandbox.openprocurement.org"
        if hasattr(self, 'file_obj') and not self.file_obj.closed:
            self.file_obj.write(req.as_bytes(True))
            self.file_obj.write("\n")
            if req.body:
                try:
                    self.file_obj.write(
                            'DATA:\n' + json.dumps(json.loads(req.body), indent=2, ensure_ascii=False).encode('utf8'))
                except ValueError:
                    pass  # doesn't write anything
                self.file_obj.write("\n")
            self.file_obj.write("\n")
        resp = super(DumpsTestAppwebtest, self).do_request(req, status=status, expect_errors=expect_errors)
        if hasattr(self, 'file_obj') and not self.file_obj.closed:
            headers = [(n.title(), v)
                       for n, v in resp.headerlist
                       if n.lower() != 'content-length']
            headers.sort()
            self.file_obj.write(str('Response: %s\n%s\n') % (
                resp.status,
                str('\n').join([str('%s: %s') % (n, v) for n, v in headers]),
            ))

            if resp.testbody:
                try:
                    self.file_obj.write(json.dumps(json.loads(resp.testbody), indent=2, ensure_ascii=False).encode('utf8'))
                except ValueError:
                    pass
            self.file_obj.write("\n\n")
        return resp


class TenderResourceTest(BaseWebTest):

    def setUp(self):
        self.app = DumpsTestAppwebtest("config:tests.ini", relative_to=os.path.dirname(base_test.__file__))
        self.app.RequestClass = PrefixedRequestClass
        self.app.authorization = ('Basic', ('broker', ''))

    def test_docs_tutorial(self):
        request_path = '/verify?{}={}'
        setup_routing(self.edr_api_app, func=response_code)

        # Basic request

        with open('docs/source/tutorial/basic_request.http', 'w') as self.app.file_obj:
            self.app.authorization = ('Basic', ('broker', ''))
            response = self.app.get(request_path.format('code', edrpou))
            self.assertEqual(response.status, '200 OK')
            self.app.file_obj.write("\n")

        setup_routing(self.edr_api_app, func=response_code)

        # request with individual tax number

        with open('docs/source/tutorial/ipn.http', 'w') as self.app.file_obj:
            self.app.authorization = ('Basic', ('broker', ''))
            response = self.app.get(request_path.format('code', ipn))
            self.assertEqual(response.status, '200 OK')
            self.app.file_obj.write("\n")

        setup_routing(self.edr_api_app, func=response_passport)

        # request with number of passport

        with open('docs/source/tutorial/passport.http', 'w') as self.app.file_obj:
            self.app.authorization = ('Basic', ('broker', ''))
            response = self.app.get(request_path.format('passport', passport.encode('utf-8')))
            self.assertEqual(response.status, '200 OK')
            self.app.file_obj.write("\n")

        setup_routing(self.edr_api_app, func=response_passport)

        # request with number of passport

        with open('docs/source/tutorial/invalid_passport.http', 'w') as self.app.file_obj:
            self.app.authorization = ('Basic', ('broker', ''))
            response = self.app.get(request_path.format('passport', invalid_passport.encode('utf-8')), status=403)
            self.assertEqual(response.status, '403 Forbidden')
            self.app.file_obj.write("\n")

        setup_routing(self.edr_api_app, func=response_code)

        # empty response

        with open('docs/source/tutorial/empty_response.http', 'w') as self.app.file_obj:
            self.app.authorization = ('Basic', ('broker', ''))
            response = self.app.get(request_path.format('code', invalid_edrpou), status=403)
            self.assertEqual(response.status, '403 Forbidden')
            self.app.file_obj.write("\n")



