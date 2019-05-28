# -*- coding: utf-8 -*-
import webtest
import os
import datetime
import iso8601
import yaml
from openprocurement.integrations.edr.tests.base import BaseWebTest, PrefixedRequestClass
from openprocurement.integrations.edr.tests._server import \
    (setup_routing, response_code, response_passport,
     check_headers, payment_required, forbidden, not_acceptable, too_many_requests, two_error_messages, bad_gateway,
     server_error, response_details, too_many_requests_details, bad_gateway_details, wrong_ip_address,
     wrong_ip_address_detailed_request, null_fields, sandbox_mode_data, sandbox_mode_data_details, DATE,
     create_long_read)
from openprocurement.integrations.edr.utils import SANDBOX_MODE, TZ, db_key
from simplejson import loads


class TestVerify(BaseWebTest):
    """ Test verify view """

    def test_opt_json(self):
        setup_routing(self.edr_api_app, func=response_code)
        response = self.app.get('/verify?id=14360570&opt_jsonp=callback')
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/javascript')
        self.assertNotIn('{\n    "', response.body)
        self.assertIn('callback({', response.body)

    def test_pretty_json(self):
        setup_routing(self.edr_api_app, func=response_code)
        response = self.app.get('/verify?id=14360570&opt_jsonp=callback&opt_pretty=1')
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/javascript')
        self.assertIn('{\n    "', response.body)
        self.assertIn('callback({', response.body)

    def test_permission_deny(self):
        old = self.app.authorization
        self.app.authorization = ('Basic', ('', ''))
        setup_routing(self.edr_api_app, func=response_code)
        response = self.app.get('/verify?id=14360570', status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'],
                         [{
                             "location": "url",
                             "name": "permission",
                             "description": "Forbidden"
                         }])
        self.app.authorization = old

    def test_edrpou(self):
        """ Get info by custom edrpou """
        setup_routing(self.edr_api_app, func=response_code)
        response = self.app.get('/verify?id=14360570')
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['meta'], {'sourceDate': '2017-04-25T11:56:36+00:00'})
        expected_data = [{u'registrationStatusDetails': u'зареєстровано',
                          u'registrationStatus': u'registered',
                          u'identification': {u'url': u'https://zqedr-api.nais.gov.ua/1.0/subjects/2842335',
                                              u'schema': u'UA-EDR',
                                              u'id': u'14360570',
                                              u'legalName': u"АКЦІОНЕРНЕ ТОВАРИСТВО КОМЕРЦІЙНИЙ БАНК \"ПРИВАТБАНК\""},
                          u'x_edrInternalId': 2842335}]
        self.assertEqual(response.json['data'], expected_data)
        response = self.app.get('/verify?id=14360570')
        if SANDBOX_MODE:
            self.assertTrue(self.redis.exists("14360570_verify_sandbox"))
            self.assertEqual(response.json, loads(self.redis.get("14360570_verify_sandbox")))
            self.assertEqual(loads(self.redis.get("14360570_verify_sandbox"))['data'], expected_data)
        else:
            self.assertTrue(self.redis.exists("14360570_verify"))
            self.assertEqual(response.json, loads(self.redis.get("14360570_verify")))
            self.assertEqual(loads(self.redis.get("14360570_verify"))['data'], expected_data)

    def test_passport(self):
        """ Get info by passport number """
        setup_routing(self.edr_api_app, func=response_passport)
        response = self.app.get('/verify?passport=СН012345')
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(
            response.json['data'],
            [{u'registrationStatusDetails': u'зареєстровано',
              u'registrationStatus': u'registered',
              u'identification': {u'url': u'https://zqedr-api.nais.gov.ua/1.0/subjects/2842336',
                                  u'schema': u'UA-EDR',
                                  u'id': u'СН012345',
                                  u'legalName': u'СН012345'},
              u'x_edrInternalId': 2842336}])

    def test_new_passport(self):
        """ Get info by new passport number with 13-digits"""
        setup_routing(self.edr_api_app, func=response_passport)
        response = self.app.get('/verify?passport=123456789')
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(
            response.json['data'],
            [{u'registrationStatusDetails': u'зареєстровано',
              u'registrationStatus': u'registered',
              u'identification': {u'url': u'https://zqedr-api.nais.gov.ua/1.0/subjects/2842336',
                                  u'schema': u'UA-EDR',
                                  u'id': u'123456789',
                                  u'legalName': u'123456789'},
              u'x_edrInternalId': 2842336}])
        self.assertEqual(response.json['meta'], DATE)

    def test_ipn(self):
        """ Get info by IPN (physical entity-entrepreneur)"""
        setup_routing(self.edr_api_app, func=response_code)
        response = self.app.get('/verify?id=1234567891')
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data'],
                         [{u'registrationStatusDetails': u'зареєстровано',
                           u'registrationStatus': u'registered',
                           u'identification': {u'url': u'https://zqedr-api.nais.gov.ua/1.0/subjects/2842335',
                                               u'schema': u'UA-EDR', u'id': u'1234567891',
                                               u'legalName': u"АКЦІОНЕРНЕ ТОВАРИСТВО КОМЕРЦІЙНИЙ БАНК \"ПРИВАТБАНК\""},
                           u'x_edrInternalId': 2842335}])
        self.assertEqual(response.json['meta'], DATE)

    def test_invalid_passport(self):
        """Check invalid passport number АБВ"""
        setup_routing(self.edr_api_app, func=response_passport)
        response = self.app.get('/verify?passport=АБВ', status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]['description'],
                         [{u'code': 11, u'message': u'`passport` parameter has wrong value.'}])

    def test_invalid_code(self):
        """Check invalid EDRPOU(IPN) number 123"""
        setup_routing(self.edr_api_app, func=response_code)
        response = self.app.get('/verify?id=123', status=404)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.status, '404 Not Found')
        expected_result = [{u'error': {u'errorDetails': u"Couldn't find this code in EDR.", u'code': u'notFound'},
                           u'meta': {u'sourceDate': u'2017-04-25T11:56:36+00:00'}}]
        self.assertEqual(response.json['errors'][0]['description'], expected_result)
        self.assertTrue(self.redis.exists(db_key("123", "verify")))
        response = self.app.get('/verify?id=123', status=404)
        self.assertEqual(response.json['errors'][0]['description'], expected_result)
        self.assertEqual(response.json, loads(self.redis.get(db_key("123", "verify"))))

    def test_unauthorized(self):
        """Send request with wrong token using tests_copy.ini conf file"""
        setup_routing(self.edr_api_app, func=check_headers)
        self.app_copy = webtest.TestApp("config:test_conf/tests_copy.ini", relative_to=os.path.dirname(__file__))
        self.app_copy.authorization = ('Basic', ('platform', 'platform'))
        self.app_copy.RequestClass = PrefixedRequestClass
        response = self.app_copy.get('/verify?id=123', status=403)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.json['errors'][0]['description'],
                         [{u'message': u'Authentication credentials were not provided.', u'code': 1}])

    def test_payment_required(self):
        """Check 402 status EDR response"""
        setup_routing(self.edr_api_app, func=payment_required)
        response = self.app.get('/verify?id=14360570', status=403)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.json['errors'][0]['description'], [{u'message': u'Payment required.', u'code': 5}])

    def test_forbidden(self):
        """Check 403 status EDR response"""
        setup_routing(self.edr_api_app, func=forbidden)
        response = self.app.get('/verify?id=14360570', status=403)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.json['errors'][0]['description'],
                         [{u'message': u'Your account is not permitted to access this resource.', u'code': 3}])

    def test_invalid_token(self):
        """Send request with invalid token 123 using new tests_copy_2.ini conf file"""
        setup_routing(self.edr_api_app, func=check_headers)
        self.app_copy = webtest.TestApp("config:test_conf/tests_copy_2.ini", relative_to=os.path.dirname(__file__))
        self.app_copy.authorization = ('Basic', ('robot', 'robot'))
        self.app_copy.RequestClass = PrefixedRequestClass
        response = self.app_copy.get('/verify?id=123', expect_errors=True)
        self.assertEqual(response.content_type, 'application/json')
        if SANDBOX_MODE:
            self.assertEqual(response.status, '404 Not Found')
            self.assertEqual(response.json['errors'][0]['description'][0]['error']['errorDetails'],
                             "Couldn't find this code in EDR.")
        else:
            self.assertEqual(response.status, '403 Forbidden')
            self.assertEqual(response.json['errors'][0]['description'],
                             [{u'code': 2, u'message': u'Invalid or expired token.'}])

    def test_bot_verify(self):
        """Send request with invalid token 123 using new tests_copy_2.ini conf file"""
        setup_routing(self.edr_api_app, func=response_code)
        setup_routing(self.edr_api_app, path='/1.0/subjects/2842335', func=response_details)
        response = self.app.get('/verify?id=14360570')
        self.assertEqual(response.status, '200 OK')
        self.assertTrue(self.redis.exists(db_key("14360570", "verify")))
        self.app.authorization = ('Basic', ('robot', 'robot'))
        response = self.app.get('/verify?id=14360570', expect_errors=True)
        expected_details_data = {u"additionalActivityKinds": [
            {u"scheme": u"КВЕД", u"id": u"64.92", u"description": u"Інші види кредитування"},
            {u"scheme": u"КВЕД", u"id": u"64.99",
             u"description": u"Надання інших фінансових послуг (крім страхування та пенсійного забезпечення), н. в. і. у."},
            {u"scheme": u"КВЕД", u"id": u"66.11", u"description": u"Управління фінансовими ринками"},
            {u"scheme": u"КВЕД", u"id": u"66.12",
             u"description": u"Посередництво за договорами по цінних паперах або товарах"},
            {u"scheme": u"КВЕД", u"id": u"66.19",
             u"description": u"Інша допоміжна діяльність у сфері фінансових послуг, крім страхування та пенсійного забезпечення"}],
            u"management": u"ЗАГАЛЬНІ ЗБОРИ", u"name": u"ПАТ КБ \"ПРИВАТБАНК\"", u"registrationStatus": u"registered",
            u"registrationStatusDetails": u"зареєстровано",
            u"identification": {u"scheme": u"UA-EDR", u"id": u"14360570",
                                u"legalName": u"АКЦІОНЕРНЕ ТОВАРИСТВО КОМЕРЦІЙНИЙ БАНК \"ПРИВАТБАНК\""},
            u"address": {u"postalCode": u"49094", u"countryName": u"УКРАЇНА",
                         u"streetAddress": u"Дніпропетровська обл., місто Дніпропетровськ, Жовтневий район"},
            u"founders": [
                {u"role_text": u"засновник", u"role": 4, u"name": u"АКЦІОНЕРИ - ЮРИДИЧНІ ТА ФІЗИЧНІ ОСОБИ"}],
            u"activityKind": {u"scheme": u"КВЕД", u"id": u"64.19",
                              u"description": u"Інші види грошового посередництва"}}
        if SANDBOX_MODE:
            self.assertEqual(response.status, '404 Not Found')
            self.assertEqual(response.json['errors'][0]['description'][0]['error']['errorDetails'],
                             "Couldn't find this code in EDR.")
            self.assertFalse(self.redis.exists(db_key("14360570", "details")))
        else:
            self.assertEqual(response.json['data'][0], expected_details_data)
            response = self.app.get('/verify?id=14360570')
            self.assertTrue(self.redis.exists(db_key("14360570", "details")))
            self.assertEqual(response.json, loads(self.redis.get(db_key("14360570", "details"))))
            self.assertEqual(loads(self.redis.get(db_key("14360570", "details")))['data'][0], expected_details_data)

    def test_not_acceptable(self):
        """Check 406 status EDR response"""
        setup_routing(self.edr_api_app, func=not_acceptable)
        response = self.app.get('/verify?id=123', status=403)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.json['errors'][0]['description'], [{u'message': u'Message.'}])

    def test_too_many_requests(self):
        """Check 429 status EDR response(too many requests)"""
        setup_routing(self.edr_api_app, func=too_many_requests)
        response = self.app.get('/verify?id=123', status=429)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.status, '429 Too Many Requests')
        self.assertEqual(response.json['errors'][0]['description'], [{u'message': u'Retry request after 26 seconds.'}])
        self.assertEqual(response.headers['Retry-After'], '26')

    def test_server_error(self):
        """Check 500 status EDR response"""
        setup_routing(self.edr_api_app, func=server_error)
        response = self.app.get('/verify?id=123', status=403)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.json['errors'][0]['description'], [{u'message': u'Internal error.', u'code': 20}])

    def test_bad_gateway(self):
        """Check 502 status EDR response"""
        setup_routing(self.edr_api_app, func=bad_gateway)
        response = self.app.get('/verify?id=123', status=403)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.json['errors'][0]['description'], [{u'message': u'Service is disabled or upgrade.'}])

    def _timeout_check_verify(self, app, delay, is_ok=True):
        setup_routing(self.edr_api_app, func=create_long_read(delay, 'verify'))
        response = app.get('/verify?id=14360570', expect_errors=True)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.status, '200 OK' if is_ok else '403 Forbidden')
        if not is_ok:
            self.assertEqual(response.json['errors'][0]['description'], [{u'message': u'Gateway Timeout Error'}])
        self.redis.flushall()

    def test_timeout_mult(self):
        """Check when EDR times out during verify - mult delay growing mode"""

        # quick response - should be ok
        self._timeout_check_verify(self.app, 0.01)
        # 3 sec delayed response - should fail (timeout setting is 2) an increase timeout x2
        self._timeout_check_verify(self.app, 3, False)
        # 5 sec delayed response - new timeout is 4 - should fail and set timeout to max 7
        self._timeout_check_verify(self.app, 5, False)
        # 8 sec delayed response - new timeout is 7 - should fail and leave timeout 7
        self._timeout_check_verify(self.app, 8, False)
        # 6.5 sec delayed response - new timeout is 7 - should succeed and set timeout to 3.5
        self._timeout_check_verify(self.app, 6.5)
        # 4 sec delayed response - new timeout is 3.5 - should fail
        self._timeout_check_verify(self.app, 4, False)

    def test_timeout_add(self):
        """Check when EDR times out during verify - add delay growing mode"""

        self.app_copy = webtest.TestApp("config:test_conf/tests_copy.ini", relative_to=os.path.dirname(__file__))
        self.app_copy.authorization = ('Basic', ('platform', 'platform'))
        self.app_copy.RequestClass = PrefixedRequestClass

        # quick response - should be ok
        self._timeout_check_verify(self.app_copy, 0.01)
        # 2 sec delayed response - should fail (timeout setting is 1) an increase timeout +2
        self._timeout_check_verify(self.app_copy, 2, False)
        # 4 sec delayed response - should fail again (timeout 3) an increase timeout +2
        self._timeout_check_verify(self.app_copy, 4, False)
        # 6 sec delayed response - should fail again (timeout 5) an increase timeout to max - 6
        self._timeout_check_verify(self.app_copy, 6, False)
        # 7 sec delayed response - should fail (timeout 6 max)
        self._timeout_check_verify(self.app_copy, 7, False)
        # 5 sec delayed response - should succeed (timeout 6) and decrease timeout to 4
        self._timeout_check_verify(self.app_copy, 5)
        # 5 sec delayed response - should fail (timeout 4)
        self._timeout_check_verify(self.app_copy, 5, False)

    def test_two_error_messages(self):
        """Check when EDR passes two errors in response"""
        setup_routing(self.edr_api_app, func=two_error_messages)
        response = self.app.get('/verify?id=123', status=403)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.json['errors'][0]['description'], [{u'code': 0, u'message': u'Message1.'},
                                                                     {u'code': 0, u'message': u'Message2.'}])

    def test_long_edrpou(self):
        setup_routing(self.edr_api_app, func=response_passport)
        response = self.app.get('/verify?passport=12345678912', status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]['description'],
                         [{u'message': u'`passport` parameter has wrong value.', u'code': 11}])

    def test_empty_request(self):
        """ Send request without params  """
        setup_routing(self.edr_api_app, func=response_passport)
        response = self.app.get('/verify', status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]['description'], [{u'message': u'Wrong name of the GET parameter'}])

    def test_accept_yaml(self):
        setup_routing(self.edr_api_app, func=response_code)
        response = self.app.get('/verify?id=14360570', headers={'Accept': 'application/yaml'})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/yaml')
        with open(os.path.join(os.path.dirname(__file__), 'test_data.yaml')) as f:
            test_yaml_data = f.read()
        self.assertEqual(response.body, test_yaml_data)

    def test_wrong_ip(self):
        setup_routing(self.edr_api_app, func=wrong_ip_address)
        response = self.app.get('/verify?id=14360570', headers={'Accept': 'application/json'}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]['description'], [{u'message': u'Forbidden'}])

    def test_sandbox_mode_data(self):
        """If SANDBOX_MODE=True define func=response_code and check that returns data from test_data_verify.json.
        Otherwise test that _server return data"""
        if SANDBOX_MODE:
            setup_routing(self.edr_api_app, func=response_code)
            response = self.app.get('/verify?id=00037256')
            self.assertEqual(response.status, '200 OK')
            self.assertEqual(response.content_type, 'application/json')
            self.assertEqual(
                response.json['data'],
                [{u'registrationStatusDetails': u'зареєстровано',
                  u'registrationStatus': u'registered',
                  u'identification': {u'url': u"https://zqedr-api.nais.gov.ua/1.0/subjects/999186",
                                      u'schema': u'UA-EDR',
                                      u'id': u'00037256',
                                      u'legalName': u"ДЕРЖАВНЕ УПРАВЛІННЯ СПРАВАМИ"},
                  u'x_edrInternalId': 999186}])
            self.assertEqual(iso8601.parse_date(response.json['meta']['sourceDate']).replace(second=0, microsecond=0),
                             datetime.datetime.now(tz=TZ).replace(second=0, microsecond=0))
        else:
            setup_routing(self.edr_api_app, func=sandbox_mode_data)
            response = self.app.get('/verify?id=00037256')
            self.assertEqual(response.status, '200 OK')
            self.assertEqual(response.content_type, 'application/json')
            self.assertEqual(
                response.json['data'],
                [{u'registrationStatusDetails': u'зареєстровано',
                  u'registrationStatus': u'registered',
                  u'identification': {u'url': u"https://zqedr-api.nais.gov.ua/1.0/subjects/999186",
                                      u'schema': u'UA-EDR',
                                      u'id': u'00037256',
                                      u'legalName': u"ДЕРЖАВНЕ УПРАВЛІННЯ СПРАВАМИ"},
                  u'x_edrInternalId': 999186}])
            self.assertEqual(response.json['meta'], DATE)


class TestDetails(BaseWebTest):
    """ Test details view """

    def setUp(self):
        self.app.authorization = ('Basic', ('robot', 'robot'))

    def test_details(self):
        """Check data for get_subject_details request"""
        setup_routing(self.edr_api_app, func=response_code)
        setup_routing(self.edr_api_app, path='/1.0/subjects/2842335', func=response_details)
        expected_data = {u"additionalActivityKinds": [
            {u"scheme": u"КВЕД", u"id": u"64.92", u"description": u"Інші види кредитування"},
            {u"scheme": u"КВЕД", u"id": u"64.99",
             u"description": u"Надання інших фінансових послуг (крім страхування та пенсійного забезпечення), н. в. і. у."},
            {u"scheme": u"КВЕД", u"id": u"66.11", u"description": u"Управління фінансовими ринками"},
            {u"scheme": u"КВЕД", u"id": u"66.12",
             u"description": u"Посередництво за договорами по цінних паперах або товарах"},
            {u"scheme": u"КВЕД", u"id": u"66.19",
             u"description": u"Інша допоміжна діяльність у сфері фінансових послуг, крім страхування та пенсійного забезпечення"}],
            u"management": u"ЗАГАЛЬНІ ЗБОРИ", u"name": u"ПАТ КБ \"ПРИВАТБАНК\"", u"registrationStatus": u"registered",
            u"registrationStatusDetails": u"зареєстровано",
            u"identification": {u"scheme": u"UA-EDR", u"id": u"14360570",
                                u"legalName": u"АКЦІОНЕРНЕ ТОВАРИСТВО КОМЕРЦІЙНИЙ БАНК \"ПРИВАТБАНК\""},
            u"address": {u"postalCode": u"49094", u"countryName": u"УКРАЇНА",
                         u"streetAddress": u"Дніпропетровська обл., місто Дніпропетровськ, Жовтневий район"},
            u"founders": [
                {u"role_text": u"засновник", u"role": 4, u"name": u"АКЦІОНЕРИ - ЮРИДИЧНІ ТА ФІЗИЧНІ ОСОБИ"}],
            u"activityKind": {u"scheme": u"КВЕД", u"id": u"64.19",
                              u"description": u"Інші види грошового посередництва"}}
        response = self.app.get('/verify?id=14360570', expect_errors=True)
        if SANDBOX_MODE:
            self.assertEqual(response.status, '404 Not Found')
            self.assertEqual(response.json['errors'][0]['description'][0]['error']['errorDetails'],
                             "Couldn't find this code in EDR.")
        else:
            self.assertTrue(self.redis.exists(db_key("14360570", "details")))
            response = self.app.get('/verify?id=14360570')
            self.assertEqual(response.json, loads(self.redis.get(db_key("14360570", "details"))))
            self.assertEqual(response.status, '200 OK')
            self.assertEqual(response.content_type, 'application/json')
            self.assertEqual(response.json['data'][0], expected_data)
            self.assertEqual(response.json['meta'], {'sourceDate': '2017-04-25T11:56:36+00:00',
                                                     'detailsSourceDate': ['2017-04-25T11:56:36+00:00']})

    def test_too_many_requests_details(self):
        """Check 429 status EDR response(too many requests) for details request"""
        setup_routing(self.edr_api_app, func=response_code)
        setup_routing(self.edr_api_app, path='/1.0/subjects/2842335', func=too_many_requests_details)
        response = self.app.get('/verify?id=14360570', expect_errors=True)
        self.assertEqual(response.content_type, 'application/json')
        if SANDBOX_MODE:
            self.assertEqual(response.status, '404 Not Found')
            self.assertEqual(response.json['errors'][0]['description'][0]['error']['errorDetails'],
                             "Couldn't find this code in EDR.")
        else:
            self.assertEqual(response.status, '429 Too Many Requests')
            self.assertEqual(response.json['errors'][0]['description'],
                             [{u'message': u'Retry request after 26 seconds.'}])
            self.assertEqual(response.headers['Retry-After'], '26')

    def test_bad_gateway_details(self):
        """Check 502 status EDR response"""
        setup_routing(self.edr_api_app, func=response_code)
        setup_routing(self.edr_api_app, path='/1.0/subjects/2842335', func=bad_gateway_details)
        response = self.app.get('/verify?id=14360570', expect_errors=True)
        self.assertEqual(response.content_type, 'application/json')
        if SANDBOX_MODE:
            self.assertEqual(response.status, '404 Not Found')
            self.assertEqual(response.json['errors'][0]['description'][0]['error']['errorDetails'],
                             "Couldn't find this code in EDR.")
        else:
            self.assertEqual(response.status, '403 Forbidden')
            self.assertEqual(response.json['errors'][0]['description'],
                             [{u'message': u'Service is disabled or upgrade.'}])

    def _timeout_check_details(self, app, delay, is_ok=True):
        setup_routing(self.edr_api_app, func=response_code)
        setup_routing(self.edr_api_app, path='/1.0/subjects/2842335', func=create_long_read(delay, 'details'))
        response = app.get('/verify?id=14360570', expect_errors=True)
        self.assertEqual(response.content_type, 'application/json')
        if SANDBOX_MODE:
            self.assertEqual(response.status, '404 Not Found')
            self.assertEqual(response.json['errors'][0]['description'][0]['error']['errorDetails'],
                             "Couldn't find this code in EDR.")
        else:
            self.assertEqual(response.status, '200 OK' if is_ok else '403 Forbidden')
            if not is_ok:
                self.assertEqual(response.json['errors'][0]['description'], [{u'message': u'Gateway Timeout Error'}])
        self.redis.flushall()

    def test_timeout_mult(self):
        """Check when EDR times out during details - mult delay growing mode"""

        # quick response - should be ok
        self._timeout_check_details(self.app, 0.2)
        # 3 sec delayed response - should fail (timeout setting is 2) an increase timeout x2
        self._timeout_check_details(self.app, 3, False)
        # 5 sec delayed response - new timeout is 4 - should fail and set timeout to max 7
        self._timeout_check_details(self.app, 5, False)
        # 8 sec delayed response - new timeout is 7 - should fail and leave timeout 7
        self._timeout_check_details(self.app, 8, False)
        # 6.5 sec delayed response - new timeout is 7 - should succeed and set timeout to 3.5
        self._timeout_check_details(self.app, 6.5)
        # 4 sec delayed response - new timeout is 3.5 - should fail
        self._timeout_check_details(self.app, 4, False)

    def test_timeout_add(self):
        """Check when EDR times out during details - add delay growing mode"""

        self.app_copy = webtest.TestApp("config:test_conf/tests_copy.ini", relative_to=os.path.dirname(__file__))
        self.app_copy.authorization = ('Basic', ('robot', 'robot'))
        self.app_copy.RequestClass = PrefixedRequestClass

        # quick response - should be ok
        self._timeout_check_details(self.app_copy, 0.2)
        # 2 sec delayed response - should fail (timeout setting is 1) an increase timeout +2
        self._timeout_check_details(self.app_copy, 2, False)
        # 4 sec delayed response - should fail again (timeout 3) an increase timeout +2
        self._timeout_check_details(self.app_copy, 4, False)
        # 6 sec delayed response - should fail again (timeout 5) an increase timeout to max - 6
        self._timeout_check_details(self.app_copy, 6, False)
        # 7 sec delayed response - should fail (timeout 6 max)
        self._timeout_check_details(self.app_copy, 7, False)
        # 5 sec delayed response - should succeed (timeout 6) and decrease timeout to 4
        self._timeout_check_details(self.app_copy, 5)
        # 5 sec delayed response - should fail (timeout 4)
        self._timeout_check_details(self.app_copy, 5, False)

    def test_accept_yaml_details(self):
        setup_routing(self.edr_api_app, func=response_code)
        setup_routing(self.edr_api_app, path='/1.0/subjects/2842335', func=response_details)
        response = self.app.get('/verify?id=14360570', headers={'Accept': 'application/yaml'}, expect_errors=True)
        self.assertEqual(response.content_type, 'application/yaml')
        if SANDBOX_MODE:
            self.assertEqual(response.status, '404 Not Found')
            self.assertEqual(yaml.load(response.body)['errors'][0]['description'][0]['error']['errorDetails'],
                             "Couldn't find this code in EDR.")
        else:
            self.assertEqual(response.status, '200 OK')
            with open(os.path.join(os.path.dirname(__file__), 'test_data_details.yaml')) as f:
                test_yaml_data = f.read()
            self.assertEqual(response.body, test_yaml_data)

    def test_wrong_ip_details(self):
        setup_routing(self.edr_api_app, func=response_code)
        setup_routing(self.edr_api_app, path='/1.0/subjects/2842335', func=wrong_ip_address_detailed_request)
        response = self.app.get('/verify?id=14360570', headers={'Accept': 'application/json'}, expect_errors=True)
        self.assertEqual(response.content_type, 'application/json')
        if SANDBOX_MODE:
            self.assertEqual(response.status, '404 Not Found')
            self.assertEqual(response.json['errors'][0]['description'][0]['error']['errorDetails'],
                             "Couldn't find this code in EDR.")
        else:
            self.assertEqual(response.status, '403 Forbidden')
            self.assertEqual(response.json['errors'][0]['description'], [{u'message': u'Forbidden'}])

    def test_null_fields(self):
        """Check that fields with null values removed"""
        setup_routing(self.edr_api_app, func=response_code)
        setup_routing(self.edr_api_app, path='/1.0/subjects/2842335', func=null_fields)
        response = self.app.get('/verify?id=14360570', expect_errors=True)
        if SANDBOX_MODE:
            self.assertEqual(response.status, '404 Not Found')
            self.assertEqual(response.json['errors'][0]['description'][0]['error']['errorDetails'],
                             "Couldn't find this code in EDR.")
        else:
            self.assertEqual(response.status, '200 OK')
            self.assertEqual(response.content_type, 'application/json')
            self.assertEqual(response.json['data'][0], {
                u"management": u"ЗАГАЛЬНІ ЗБОРИ",
                u"registrationStatus": u"registered",
                u"registrationStatusDetails": u"зареєстровано",
                u"identification": {u"scheme": u"UA-EDR",
                                    u"id": u"14360570"},
                u"address": {u"postalCode": u"49094",
                             u"countryName": u"УКРАЇНА",
                             u"streetAddress": u"Дніпропетровська обл., місто Дніпропетровськ, Жовтневий район"},
                u"founders": [{
                    u"role_text": u"засновник",
                    u"role": 4,
                    u"name": u"АКЦІОНЕРИ - ЮРИДИЧНІ ТА ФІЗИЧНІ ОСОБИ",
                }],
                u"activityKind": {u"scheme": u"КВЕД",
                                  u"id": u"64.19",
                                  u"description": u"Інші види грошового посередництва"}})
            self.assertEqual(response.json['meta'], {'sourceDate': '2017-04-25T11:56:36+00:00',
                                                     'detailsSourceDate': ['2017-04-25T11:56:36+00:00']})

    def test_sandbox_mode_data_details(self):
        """If SANDBOX_MODE=True define func=response_code and check that returns data from test_data_details.json.
        Otherwise test that _server return data"""
        example_data = [{
            u"management": u"КЕРІВНИК",
            u"name": u"ДЕРЖАВНЕ УПРАВЛІННЯ СПРАВАМИ",
            u"registrationStatus": u"registered",
            u"registrationStatusDetails": u"зареєстровано",
            u"identification": {
                u"scheme": u"UA-EDR",
                u"id": u"00037256",
                u"legalName": u"ДЕРЖАВНЕ УПРАВЛІННЯ СПРАВАМИ"
            },
            u"address": {
                u"postalCode": u"01220",
                u"countryName": u"УКРАЇНА",
                u"streetAddress": u"м.Київ, Печерський район ВУЛИЦЯ БАНКОВА буд. 11"
            },
            u"founders": [
                {
                    u"role_text": u"засновник",
                    u"role": 4,
                    u"name": u"УКАЗ ПРИЗИДЕНТА УКРАЇНИ №278/2000 ВІД 23 ЛЮТОГО 2000 РОКУ"
                }
            ],
            u"activityKind": {
                u"scheme": u"КВЕД",
                u"id": u"84.11",
                u"description": u"Державне управління загального характеру"
            }}]
        if SANDBOX_MODE:
            response = self.app.get('/verify?id=00037256')
            self.assertEqual(response.status, '200 OK')
            self.assertEqual(response.content_type, 'application/json')
            self.assertEqual(response.json['data'], example_data)
            self.assertEqual(iso8601.parse_date(response.json['meta']['sourceDate']).replace(second=0, microsecond=0),
                             datetime.datetime.now(tz=TZ).replace(second=0, microsecond=0))
        else:
            setup_routing(self.edr_api_app, func=sandbox_mode_data)
            setup_routing(self.edr_api_app, path='/1.0/subjects/999186', func=sandbox_mode_data_details)
            response = self.app.get('/verify?id=00037256')
            self.assertEqual(response.status, '200 OK')
            self.assertEqual(response.content_type, 'application/json')
            self.assertEqual(response.json['data'][0], example_data[0])
            self.assertEqual(response.json['meta'], {'sourceDate': '2017-04-25T11:56:36+00:00',
                                                     'detailsSourceDate': ['2017-04-25T11:56:36+00:00']})

    def test_invalid_code(self):
        """Check invalid EDRPOU(IPN) number 123"""
        setup_routing(self.edr_api_app, func=response_code)
        response = self.app.get('/verify?id=123', status=404)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.status, '404 Not Found')
        expected_result = [{u'error': {u'errorDetails': u"Couldn't find this code in EDR.", u'code': u'notFound'},
                           u'meta': {u'sourceDate': u'2017-04-25T11:56:36+00:00'}}]
        if SANDBOX_MODE:
            self.assertEqual(response.json['errors'][0]['description'][0]['error']['errorDetails'],
                             "Couldn't find this code in EDR.")
        else:
            self.assertTrue(self.redis.exists(db_key("123", "verify")))
            self.assertEqual(response.json['errors'][0]['description'], expected_result)
            response = self.app.get('/verify?id=123', status=404)
            self.assertEqual(response.json, loads(self.redis.get(db_key("123", "verify"))))
