# -*- coding: utf-8 -*-
import webtest
import os
import datetime
import iso8601

from openprocurement.integrations.edr.tests.base import BaseWebTest, PrefixedRequestClass
from openprocurement.integrations.edr.tests._server import (setup_routing, response_code, response_passport,
                                                            check_headers, payment_required, forbidden, not_acceptable,
                                                            too_many_requests, two_error_messages, bad_gateway,
                                                            server_error, response_details, too_many_requests_details,
                                                            bad_gateway_details, wrong_ip_address,
                                                            wrong_ip_address_detailed_request, null_fields,
                                                            sandbox_mode_data, sandbox_mode_data_details)
from openprocurement.integrations.edr.utils import SANDBOX_MODE, TZ, meta_data
from pytz import UTC
import yaml


def time_mismatch(r_date):
    sample_time = meta_data(datetime.datetime.now().replace(tzinfo=UTC).strftime('%a, %d %b %Y %H:%M:%S %Z'))
    if sample_time == r_date:
        return sample_time
    else:
        return r_date


class TestVerify(BaseWebTest):
    """ Test verify view """

    def test_opt_json(self):
        setup_routing(self.edr_api_app, func=response_code)
        response = self.app.get('/verify?id=14360570&opt_jsonp=callback', expect_errors=True)
        if SANDBOX_MODE:
            self.assertEqual(response.status, '404 Not Found')
            self.assertIn("Couldn't find this code in EDR.", response.body)
        else:
            self.assertEqual(response.content_type, 'application/javascript')
            self.assertEqual(response.status, '200 OK')
            self.assertNotIn('{\n    "', response.body)
            self.assertIn('callback({', response.body)

    def test_pretty_json(self):
        setup_routing(self.edr_api_app, func=response_code)
        response = self.app.get('/verify?id=14360570&opt_jsonp=callback&opt_pretty=1', expect_errors=True)
        if SANDBOX_MODE:
            self.assertEqual(response.status, '404 Not Found')
            self.assertIn("Couldn't find this code in EDR.", response.body)
        else:
            self.assertEqual(response.content_type, 'application/javascript')
            self.assertEqual(response.status, '200 OK')
            self.assertIn('{\n    "', response.body)
            self.assertIn('callback({', response.body)

    def test_permission_deny(self):
        old = self.app.authorization
        self.app.authorization = ('Basic', ('', ''))
        setup_routing(self.edr_api_app, func=response_code)
        response = self.app.get('/verify?id=14360570', status=403)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.json['errors'],
                         [{
                             "location": "url",
                             "name": "permission",
                             "description": "Forbidden"
                         }]
                         )
        self.app.authorization = old

    def test_edrpou(self):
        """ Get info by custom edrpou """
        setup_routing(self.edr_api_app, func=response_code)
        response = self.app.get('/verify?id=14360570', expect_errors=True)
        self.assertEqual(response.content_type, 'application/json')
        if SANDBOX_MODE:
            self.assertEqual(response.status, '404 Not Found')
            self.assertIn(response.json['errors'][0]['description'][0]['error']['errorDetails'],
                          "Couldn't find this code in EDR.")
        else:
            self.assertEqual(response.status, '200 OK')
            self.assertEqual(response.json['meta'], time_mismatch(response.json['meta']))
            self.assertEqual(response.json['data'],
                             [{u'registrationStatusDetails': u'зареєстровано',
                               u'registrationStatus': u'registered',
                               u'identification': {u'url': u'https://zqedr-api.nais.gov.ua/1.0/subjects/2842335',
                                                   u'schema': u'UA-EDR',
                                                   u'id': u'14360570',
                                                   u'legalName': u"АКЦІОНЕРНЕ ТОВАРИСТВО КОМЕРЦІЙНИЙ БАНК \"ПРИВАТБАНК\""},
                               u'x_edrInternalId': 2842335}])

    def test_passport(self):
        """ Get info by passport number """
        setup_routing(self.edr_api_app, func=response_passport)
        response = self.app.get('/verify?passport=СН012345', expect_errors=True)
        self.assertEqual(response.content_type, 'application/json')
        if SANDBOX_MODE:
            self.assertEqual(response.status, '404 Not Found')
            self.assertEqual(response.json['errors'][0]['description'][0]['error']['errorDetails'],
                             "Couldn't find this code in EDR.")
        else:
            self.assertEqual(response.status, '200 OK')
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
        response = self.app.get('/verify?passport=123456789', expect_errors=True)
        self.assertEqual(response.content_type, 'application/json')
        if SANDBOX_MODE:
            self.assertEqual(response.status, '404 Not Found')
            self.assertEqual(response.json['errors'][0]['description'][0]['error']['errorDetails'],
                             "Couldn't find this code in EDR.")
        else:
            self.assertEqual(response.status, '200 OK')
            self.assertEqual(
                response.json['data'],
                [{u'registrationStatusDetails': u'зареєстровано',
                  u'registrationStatus': u'registered',
                  u'identification': {u'url': u'https://zqedr-api.nais.gov.ua/1.0/subjects/2842336',
                                      u'schema': u'UA-EDR',
                                      u'id': u'123456789',
                                      u'legalName': u'123456789'},
                  u'x_edrInternalId': 2842336}])
            self.assertEqual(response.json['meta'], time_mismatch(response.json['meta']))

    def test_ipn(self):
        """ Get info by IPN (physical entity-entrepreneur)"""
        setup_routing(self.edr_api_app, func=response_code)
        response = self.app.get('/verify?id=1234567891', expect_errors=True)
        self.assertEqual(response.content_type, 'application/json')
        if SANDBOX_MODE:
            self.assertEqual(response.status, '404 Not Found')
            self.assertEqual(response.json['errors'][0]['description'][0]['error']['errorDetails'],
                             "Couldn't find this code in EDR.")
        else:
            self.assertEqual(response.status, '200 OK')
            self.assertEqual(response.json['data'],
                             [{u'registrationStatusDetails': u'зареєстровано',
                               u'registrationStatus': u'registered',
                               u'identification': {u'url': u'https://zqedr-api.nais.gov.ua/1.0/subjects/2842335',
                                                   u'schema': u'UA-EDR', u'id': u'1234567891',
                                                   u'legalName': u"АКЦІОНЕРНЕ ТОВАРИСТВО КОМЕРЦІЙНИЙ БАНК \"ПРИВАТБАНК\""},
                               u'x_edrInternalId': 2842335}])
            self.assertEqual(response.json['meta'], time_mismatch(response.json['meta']))

    def test_invalid_passport(self):
        """Check invalid passport number АБВ"""
        setup_routing(self.edr_api_app, func=response_passport)
        response = self.app.get('/verify?passport=АБВ', expect_errors=True)
        self.assertEqual(response.content_type, 'application/json')
        if SANDBOX_MODE:
            self.assertEqual(response.status, '404 Not Found')
            self.assertEqual(response.json['errors'][0]['description'][0]['error']['errorDetails'],
                             "Couldn't find this code in EDR.")
        else:
            self.assertEqual(response.status, '403 Forbidden')
            self.assertEqual(response.json['errors'][0]['description'],
                             [{u'code': 11, u'message': u'`passport` parameter has wrong value.'}])

    def test_invalid_code(self):
        """Check invalid EDRPOU(IPN) number 123"""
        setup_routing(self.edr_api_app, func=response_code)
        response = self.app.get('/verify?id=123', status=404)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.json['errors'][0]['description'],
                         time_mismatch(response.json['errors'][0]['description']))

    def test_unauthorized(self):
        """Send request without token using tests_copy.ini conf file"""
        setup_routing(self.edr_api_app, func=check_headers)
        self.app_copy = webtest.TestApp("config:test_conf/tests_copy.ini", relative_to=os.path.dirname(__file__))
        self.app_copy.authorization = ('Basic', ('platform', 'platform'))
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
                             [{u'message': u'Authentication credentials were not provided.', u'code': 1}])

    def test_payment_required(self):
        """Check 402 status EDR response"""
        setup_routing(self.edr_api_app, func=payment_required)
        response = self.app.get('/verify?id=14360570', expect_errors=True)
        if SANDBOX_MODE:
            self.assertEqual(response.status, '404 Not Found')
            self.assertEqual(response.json['errors'][0]['description'][0]['error']['errorDetails'],
                             "Couldn't find this code in EDR.")
        else:
            self.assertEqual(response.content_type, 'application/json')
            self.assertEqual(response.status, '403 Forbidden')
            self.assertEqual(response.json['errors'][0]['description'],
                             [{u'message': u'Payment required.', u'code': 5}])

    def test_forbidden(self):
        """Check 403 status EDR response"""
        setup_routing(self.edr_api_app, func=forbidden)
        response = self.app.get('/verify?id=14360570', expect_errors=True)
        self.assertEqual(response.content_type, 'application/json')
        if SANDBOX_MODE:
            self.assertEqual(response.status, '404 Not Found')
            self.assertEqual(response.json['errors'][0]['description'][0]['error']['errorDetails'],
                             "Couldn't find this code in EDR.")
        else:
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

    def test_not_acceptable(self):
        """Check 406 status EDR response"""
        setup_routing(self.edr_api_app, func=not_acceptable)
        response = self.app.get('/verify?id=123', expect_errors=True)
        if SANDBOX_MODE:
            self.assertEqual(response.status, '404 Not Found')
            self.assertEqual(response.json['errors'][0]['description'][0]['error']['errorDetails'],
                             "Couldn't find this code in EDR.")
        else:
            self.assertEqual(response.content_type, 'application/json')
            self.assertEqual(response.status, '403 Forbidden')
            self.assertEqual(response.json['errors'][0]['description'], [{u'message': u'Message.'}])

    def test_too_many_requests(self):
        """Check 429 status EDR response(too many requests)"""
        setup_routing(self.edr_api_app, func=too_many_requests)
        response = self.app.get('/verify?id=123', expect_errors=True)
        if SANDBOX_MODE:
            self.assertEqual(response.status, '404 Not Found')
            self.assertEqual(response.json['errors'][0]['description'][0]['error']['errorDetails'],
                             "Couldn't find this code in EDR.")
        else:
            self.assertEqual(response.content_type, 'application/json')
            self.assertEqual(response.status, '429 Too Many Requests')
            self.assertEqual(response.json['errors'][0]['description'],
                             [{u'message': u'Retry request after 26 seconds.'}])
            self.assertEqual(response.headers['Retry-After'], '26')

    def test_server_error(self):
        """Check 500 status EDR response"""
        setup_routing(self.edr_api_app, func=server_error)
        response = self.app.get('/verify?id=123', expect_errors=True)
        if SANDBOX_MODE:
            self.assertEqual(response.status, '404 Not Found')
            self.assertEqual(response.json['errors'][0]['description'][0]['error']['errorDetails'],
                             "Couldn't find this code in EDR.")
        else:
            self.assertEqual(response.content_type, 'application/json')
            self.assertEqual(response.status, '403 Forbidden')
            self.assertEqual(response.json['errors'][0]['description'], [{u'message': u'Internal error.', u'code': 20}])

    def test_bad_gateway(self):
        """Check 502 status EDR response"""
        setup_routing(self.edr_api_app, func=bad_gateway)
        response = self.app.get('/verify?id=123', expect_errors=True)
        if SANDBOX_MODE:
            self.assertEqual(response.status, '404 Not Found')
            self.assertEqual(response.json['errors'][0]['description'][0]['error']['errorDetails'],
                             "Couldn't find this code in EDR.")
        else:
            self.assertEqual(response.content_type, 'application/json')
            self.assertEqual(response.status, '403 Forbidden')
            self.assertEqual(response.json['errors'][0]['description'],
                             [{u'message': u'Service is disabled or upgrade.'}])

    def test_two_error_messages(self):
        """Check when EDR passes two errors in response"""
        setup_routing(self.edr_api_app, func=two_error_messages)
        response = self.app.get('/verify?id=123', expect_errors=True)
        if SANDBOX_MODE:
            self.assertEqual(response.status, '404 Not Found')
            self.assertEqual(response.json['errors'][0]['description'][0]['error']['errorDetails'],
                             "Couldn't find this code in EDR.")
        else:
            self.assertEqual(response.content_type, 'application/json')
            self.assertEqual(response.status, '403 Forbidden')
            self.assertEqual(response.json['errors'][0]['description'], [{u'code': 0, u'message': u'Message1.'},
                                                                         {u'code': 0, u'message': u'Message2.'}])

    def test_long_edrpou(self):
        setup_routing(self.edr_api_app, func=response_passport)
        response = self.app.get('/verify?passport=12345678912', expect_errors=True)
        self.assertEqual(response.content_type, 'application/json')
        if SANDBOX_MODE:
            self.assertEqual(response.status, '404 Not Found')
            self.assertEqual(response.json['errors'][0]['description'][0]['error']['errorDetails'],
                             "Couldn't find this code in EDR.")
        else:
            self.assertEqual(response.status, '403 Forbidden')
            self.assertEqual(response.json['errors'][0]['description'],
                             [{u'message': u'`passport` parameter has wrong value.', u'code': 11}])

    def test_empty_request(self):
        """ Send request without params  """
        setup_routing(self.edr_api_app, func=response_passport)
        response = self.app.get('/verify', expect_errors=True)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.json['errors'][0]['description'], [{u'message': u'Wrong name of the GET parameter'}])

    def test_accept_yaml(self):
        setup_routing(self.edr_api_app, func=response_code)
        response = self.app.get('/verify?id=14360570', headers={'Accept': 'application/yaml'}, expect_errors=True)
        if SANDBOX_MODE:
            self.assertEqual(response.status, '404 Not Found')
            self.assertEqual(yaml.load(response.body)['errors'][0]['description'][0]['error']['errorDetails'],
                             "Couldn't find this code in EDR.")
        else:
            self.assertEqual(response.status, '200 OK')
            with open(os.path.join(os.path.dirname(__file__), 'test_data.yaml'), 'r') as f:
                test_yaml_data = f.read()
                data = yaml.load(test_yaml_data)
                data['meta'].update(yaml.load(response.body)['meta'])
            self.assertEqual(response.body, yaml.safe_dump(data, allow_unicode=True, default_flow_style=False))
            self.assertEqual(response.content_type, 'application/yaml')

    def test_wrong_ip(self):
        setup_routing(self.edr_api_app, func=wrong_ip_address)
        response = self.app.get('/verify?id=14360570', headers={'Accept': 'application/json'}, expect_errors=True)
        if SANDBOX_MODE:
            self.assertEqual(response.status, '404 Not Found')
            self.assertEqual(response.json['errors'][0]['description'][0]['error']['errorDetails'],
                             "Couldn't find this code in EDR.")
        else:
            self.assertEqual(response.status, '403 Forbidden')
            self.assertEqual(response.json['errors'][0]['description'], [{u'message': u'Forbidden'}])
        self.assertEqual(response.content_type, 'application/json')

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
            response = self.app.get('/verify?id=00037256', expect_errors=True)
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
            self.assertEqual(response.json['meta'], time_mismatch(response.json['meta']))


class TestDetails(BaseWebTest):
    """ Test details view """

    def setUp(self):
        self.app.authorization = ('Basic', ('robot', 'robot'))

    def test_details(self):
        """Check data for get_subject_details request"""
        setup_routing(self.edr_api_app, func=response_code)
        setup_routing(self.edr_api_app, path='/1.0/subjects/2842335', func=response_details)
        response = self.app.get('/verify?id=14360570', expect_errors=True)
        if SANDBOX_MODE:
            self.assertEqual(response.status, '404 Not Found')
            self.assertEqual(response.json['errors'][0]['description'][0]['error']['errorDetails'],
                             "Couldn't find this code in EDR.")
            self.assertEqual(response.json['errors'][0]['description'][0]['meta'],
                             time_mismatch(response.json['errors'][0]['description'][0]['meta']))
        else:
            self.assertEqual(response.status, '200 OK')
            self.assertEqual(response.content_type, 'application/json')
            self.assertEqual(response.json[0]['data'], {
                u"additionalActivityKinds": [
                    {u"scheme": u"КВЕД",
                     u"id": u"64.92",
                     u"description": u"Інші види кредитування"},
                    {u"scheme": u"КВЕД",
                     u"id": u"64.99",
                     u"description": u"Надання інших фінансових послуг (крім страхування та пенсійного забезпечення), н. в. і. у."},
                    {u"scheme": u"КВЕД",
                     u"id": u"66.11",
                     u"description": u"Управління фінансовими ринками"},
                    {u"scheme": u"КВЕД",
                     u"id": u"66.12",
                     u"description": u"Посередництво за договорами по цінних паперах або товарах"},
                    {u"scheme": u"КВЕД",
                     u"id": u"66.19",
                     u"description": u"Інша допоміжна діяльність у сфері фінансових послуг, крім страхування та пенсійного забезпечення"}],
                u"management": u"ЗАГАЛЬНІ ЗБОРИ",
                u"name": u"ПАТ КБ \"ПРИВАТБАНК\"",
                u"registrationStatus": u"registered",
                u"registrationStatusDetails": u"зареєстровано",
                u"identification": {u"scheme": u"UA-EDR",
                                    u"id": u"14360570",
                                    u"legalName": u"АКЦІОНЕРНЕ ТОВАРИСТВО КОМЕРЦІЙНИЙ БАНК \"ПРИВАТБАНК\""},
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
                                  u"description": u"Інші види грошового посередництва"}
            })
            self.assertEqual(response.json[0]['meta'], time_mismatch(response.json[0]['meta']))

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

    def test_accept_yaml_details(self):
        setup_routing(self.edr_api_app, func=response_code)
        setup_routing(self.edr_api_app, path='/1.0/subjects/2842335', func=response_details)
        response = self.app.get('/verify?id=14360570', headers={'Accept': 'application/yaml'}, expect_errors=True)
        if SANDBOX_MODE:
            self.assertEqual(response.status, '404 Not Found')
            self.assertEqual(yaml.load(response.body)['errors'][0]['description'][0]['error']['errorDetails'],
                             "Couldn't find this code in EDR.")
        else:
            self.assertEqual(response.status, '200 OK')
            with open(os.path.join(os.path.dirname(__file__), 'test_data_details.yaml'), 'r') as f:
                test_yaml_data = f.read()
                data = yaml.load(test_yaml_data)
                data[0]['meta'].update(yaml.load(response.body)[0]['meta'])
            self.assertEqual(response.body, yaml.safe_dump(data, allow_unicode=True, default_flow_style=False))
            self.assertEqual(response.content_type, 'application/yaml')

    def test_wrong_ip_details(self):
        setup_routing(self.edr_api_app, func=response_code)
        setup_routing(self.edr_api_app, path='/1.0/subjects/2842335', func=wrong_ip_address_detailed_request)
        response = self.app.get('/verify?id=14360570', headers={'Accept': 'application/json'}, expect_errors=True)
        if SANDBOX_MODE:
            self.assertEqual(response.status, '404 Not Found')
            self.assertEqual(response.json['errors'][0]['description'][0]['error']['errorDetails'],
                             "Couldn't find this code in EDR.")
        else:
            self.assertEqual(response.status, '403 Forbidden')
            self.assertEqual(response.content_type, 'application/json')
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
            self.assertEqual(response.json[0]['data'], {
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
            self.assertEqual(response.json[0]['meta'], time_mismatch(response.json[0]['meta']))

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
            setup_routing(self.edr_api_app, func=response_code)
            setup_routing(self.edr_api_app, path='/1.0/subjects/999186', func=response_details)
            response = self.app.get('/verify?id=00037256')
            self.assertEqual(response.status, '200 OK')
            self.assertEqual(response.content_type, 'application/json')
            self.assertEqual(response.json['data'], example_data)
            self.assertEqual(
                iso8601.parse_date(response.json['meta']['sourceDate']).replace(second=0, microsecond=0),
                datetime.datetime.now(tz=TZ).replace(second=0, microsecond=0))
        else:
            setup_routing(self.edr_api_app, func=sandbox_mode_data)
            setup_routing(self.edr_api_app, path='/1.0/subjects/999186', func=sandbox_mode_data_details)
            response = self.app.get('/verify?id=00037256')
            self.assertEqual(response.status, '200 OK')
            self.assertEqual(response.content_type, 'application/json')
            self.assertEqual(response.json[0]['data'], example_data[0])
            self.assertEqual(response.json[0]['meta'], time_mismatch(response.json[0]['meta']))
