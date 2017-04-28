# -*- coding: utf-8 -*-
import requests
from collections import namedtuple
from pyramid.view import view_config
from logging import getLogger
from openprocurement.integrations.edr.utils import prepare_data_details, prepare_data, error_handler

LOGGER = getLogger(__name__)
EDRDetails = namedtuple("EDRDetails", ['param', 'code'])


def handle_error(request, message, status=403):
    LOGGER.info('Error on processing request "{}"'.format(message))
    return error_handler(request, status, {"location": "body",
                                        "name": "data",
                                        "description": message})


@view_config(route_name='verify', renderer='json',
             request_method='GET', permission='verify')
def verify_user(request):
    code = request.params.get('id', '').encode('utf-8')
    details = EDRDetails('code', code)
    if not code:
        passport = request.params.get('passport', '').encode('utf-8')
        if not passport:
            return handle_error(request, [{u'message': u'Need pass id or passport'}])
        details = EDRDetails('passport', passport)
    try:
        response = request.registry.edr_client.get_subject(**details._asdict())
    except (requests.exceptions.ReadTimeout,
            requests.exceptions.ConnectTimeout):
        return handle_error(request, [{u'message': u'Gateway Timeout Error'}])
    if response.headers['Content-Type'] != 'application/json':
        return handle_error(request, [{u'message': u'Forbidden'}])
    if response.status_code == 200:
        data = response.json()
        if not data:
            LOGGER.warning('Accept empty response from EDR service for {}'.format(details.code))
            return handle_error(request, [{u'message': u'EDRPOU not found'}], 404)
        LOGGER.info('Return data from EDR service for {}'.format(details.code))
        return {'data': [prepare_data(d) for d in data]}
    elif response.status_code == 429:
        request.response.headers['Retry-After'] = response.headers.get('Retry-After')
        return handle_error(request, [{u'message': u'Retry request after {} seconds.'.format(response.headers.get('Retry-After'))}], status=429)
    elif response.status_code == 502:
        return handle_error(request, [{u'message': u'Service is disabled or upgrade.'}])
    else:
        return handle_error(request, response.json()['errors'])


@view_config(route_name='details', renderer='json',
             request_method='GET', permission='get_details')
def user_details(request):
    id = request.matchdict.get('id')
    try:
        response = request.registry.edr_client.get_subject_details(id)
    except (requests.exceptions.ReadTimeout,
            requests.exceptions.ConnectTimeout):
        return handle_error(request, [{u'message': u'Gateway Timeout Error'}])
    if response.headers['Content-Type'] != 'application/json':
        return handle_error(request, [{u'message': u'Forbidden'}])
    if response.status_code == 200:
        data = response.json()
        LOGGER.info('Return detailed data from EDR service for {}'.format(id))
        return {'data': prepare_data_details(data)}
    elif response.status_code == 429:
        request.response.headers['Retry-After'] = response.headers.get('Retry-After')
        return handle_error(request, [{u'message': u'Retry request after {} seconds.'.format(response.headers.get('Retry-After'))}], status=429)
    elif response.status_code == 502:
        return handle_error(request, [{u'message': u'Service is disabled or upgrade.'}])
    else:
        return handle_error(request, response.json()['errors'])