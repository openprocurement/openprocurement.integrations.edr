# -*- coding: utf-8 -*-
import requests
from collections import namedtuple
from pyramid.view import view_config
from logging import getLogger

LOGGER = getLogger(__name__)
EDRDetails = namedtuple("EDRDetails", ['param', 'code'])
identification_schema = u'UA-EDR'


def handle_error(request, message):
    request.errors.add('body', 'data', message)
    LOGGER.info('Error on processing request "{}"'.format(message))
    request.response.status = 403
    return {
        "status": "error",
        "errors": request.errors
    }


def prepare_data(data):
    return {'id': data.get('id'),
            'state': {'code': data.get('state'),
                      'description': data.get('state_text')},
            'identification': {'schema': identification_schema,
                               'id': data.get('code'),
                               'legalName': data.get('name'),
                               'url': data.get('url')}}


@view_config(route_name='verify', renderer='json',
             request_method='GET', permission='verify')
def verify_user(request):
    code = request.params.get('code', '').encode('utf-8')
    details = EDRDetails('code', code)
    if not code:
        passport = request.params.get('passport', '').encode('utf-8')
        if not passport:
            return handle_error(request, [{u'message': u'Need pass code or passport'}])
        details = EDRDetails('passport', passport)
    try:
        response = request.registry.edr_client.get_subject(**details._asdict())
    except (requests.exceptions.ReadTimeout,
            requests.exceptions.ConnectTimeout):
        return handle_error(request, [{u'message': u'Gateway Timeout Error'}])
    if response.status_code == 200:
        data = response.json()
        if not data:
            LOGGER.warning('Accept empty response from EDR service for {}'.format(details.code))
            return handle_error(request, [{u'message': u'EDRPOU not found'}])
        LOGGER.info('Return data from EDR service for {}'.format(details.code))
        return {'data': prepare_data(data)}
    elif response.status_code == 429:
        return handle_error(request, [{u'message': u'Retry request after {} seconds.'.format(response.headers.get('Retry-After'))}])
    elif response.status_code == 502:
        return handle_error(request, [{u'message': u'Service is disabled or upgrade.'}])
    else:
        return handle_error(request, response.json()['errors'])

