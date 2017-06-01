# -*- coding: utf-8 -*-
import requests
from collections import namedtuple
from pyramid.view import view_config
from logging import getLogger
from datetime import datetime
from openprocurement.integrations.edr.utils import prepare_data_details, prepare_data, error_handler, SANDBOX_MODE, \
    TEST_DATA_VERIFY, TEST_DATA_DETAILS, meta_data, TZ


LOGGER = getLogger(__name__)
EDRDetails = namedtuple("EDRDetails", ['param', 'code'])
default_error_status = 403
error_message = {u"errorDetails": u"Couldn't find this code in EDR.", u"code": u"notFound"}


def handle_error(request, response):
    if response.headers['Content-Type'] != 'application/json':
        return error_handler(request, default_error_status,
                             {"location": "request", "name": "ip",
                              "description": [{u'message': u'Content-Type of EDR API response is not application/json'}]})
    if response.status_code == 429:
        seconds_to_wait = response.headers.get('Retry-After')
        request.response.headers['Retry-After'] = seconds_to_wait
        return error_handler(request, 429, {"location": "body", "name": "data",
                                            "description": [{u'message': u'Retry request after {} seconds.'.format(seconds_to_wait)}]})
    elif response.status_code == 502:
        return error_handler(request, default_error_status, {"location": "body",
                                                             "name": "data",
                                                             "description": [{u'message': u'Service is disabled or upgrade.'}]})
    return error_handler(request, default_error_status, {"location": "body",
                                                         "name": "data",
                                                         "description": response.json()['errors']})


@view_config(route_name='verify', renderer='json',
             request_method='GET', permission='verify')
def verify_user(request):
    code = request.params.get('id', '').encode('utf-8')
    details = EDRDetails('code', code)
    role = request.authenticated_role
    if not code:
        passport = request.params.get('passport', '').encode('utf-8')
        if not passport:
            return error_handler(request, default_error_status, {"location": "url", "name": "id",
                                                                 "description": [{u'message': u'Wrong name for the GET parameter'}]})
        details = EDRDetails('passport', passport)
    if SANDBOX_MODE:
        if role == 'robots' and TEST_DATA_DETAILS.get(code):
            LOGGER.info('Return test data for {} for bot'.format(code))
            return [{'data': prepare_data_details(TEST_DATA_DETAILS[code]),
                    'meta': {'sourceDate': datetime.now(tz=TZ).isoformat()}}]
        elif TEST_DATA_VERIFY.get(code):
            LOGGER.info('Return test data for {} for platform'.format(code))
            return {'data': [prepare_data(d) for d in TEST_DATA_VERIFY[code]],
                    'meta': {'sourceDate': datetime.now(tz=TZ).isoformat()}}
    try:
        response = request.registry.edr_client.get_subject(**details._asdict())
    except (requests.exceptions.ReadTimeout,
            requests.exceptions.ConnectTimeout):
        return error_handler(request, default_error_status, {"location": "url", "name": "id",
                                                             "description": [{u'message': u'Gateway Timeout Error'}]})
    if response.status_code == 200:
        data = response.json()
        if not data:
            LOGGER.warning('Accept empty response from EDR service for {}'.format(details.code))
            return error_handler(request, 404, {"location": "body", "name": "data",
                                                "description": [{u"error": error_message,
                                                                 u'meta': meta_data(response.headers['Date'])}]})
        if role == 'robots':  # send second request for edr-bot
            data_details = []
            for obj in data:
                try:
                    details_response = request.registry.edr_client.get_subject_details(obj['id'])
                except (requests.exceptions.ReadTimeout,
                        requests.exceptions.ConnectTimeout):
                    return error_handler(request, default_error_status, {"location": "url", "name": "id",
                                                                         "description": [{u'message': u'Gateway Timeout Error'}]})
                if details_response.status_code != 200:

                    return handle_error(request, details_response)
                else:
                    LOGGER.info('Return detailed data from EDR service for {}'.format(obj['id']))
                    data_details.append({'data': prepare_data_details(details_response.json()), 'meta': meta_data(details_response.headers['Date'])})
            return data_details
        LOGGER.info('Return data from EDR service for {}'.format(details.code))
        return {'data': [prepare_data(d) for d in data], 'meta': meta_data(response.headers['Date'])}
    else:
        return handle_error(request, response)

