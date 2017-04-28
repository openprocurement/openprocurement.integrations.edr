# -*- coding: utf-8 -*-
import os
from logging import getLogger
from json import dumps
from pkg_resources import get_distribution
from webob.multidict import NestedMultiDict
from datetime import datetime
from pytz import timezone, UTC
from hashlib import sha512
from ConfigParser import ConfigParser
from pyramid.security import Allow
from pyramid.httpexceptions import exception_response


PKG = get_distribution(__package__)
LOGGER = getLogger(PKG.project_name)
VERSION = '{}.{}'.format(int(PKG.parsed_version[0]), int(PKG.parsed_version[1]) if PKG.parsed_version[1].isdigit() else 0)
TZ = timezone(os.environ['TZ'] if 'TZ' in os.environ else 'Europe/Kiev')
USERS = {}
identification_schema = u'UA-EDR'
activityKind_scheme = u'КВЕД'
SANDBOX_MODE = os.environ.get('SANDBOX_MODE', False)


class Root(object):
    __name__ = None
    __parent__ = None
    __acl__ = [
        (Allow, 'g:platforms', 'verify'),
        (Allow, 'g:robots', 'verify'),
        (Allow, 'g:robots', 'get_details'),
    ]

    def __init__(self, request):
        self.request = request


def read_users(filename):
    config = ConfigParser()
    config.read(filename)
    for i in config.sections():
        USERS.update(dict([
            (
                j,
                {
                    'password': k,
                    'group': i
                }
            )
            for j, k in config.items(i)
        ]))


def get_now():
    return datetime.now(TZ)


def update_logging_context(request, params):
    if not request.__dict__.get('logging_context'):
        request.logging_context = {}

    for x, j in params.items():
        request.logging_context[x.upper()] = j


def context_unpack(request, msg, params=None):
    if params:
        update_logging_context(request, params)
    logging_context = request.logging_context
    journal_context = msg
    for key, value in logging_context.items():
        journal_context["JOURNAL_" + key] = value
    return journal_context


def error_handler(request, status, error):
    params = {
        'ERROR_STATUS': status
    }
    for key, value in error.items():
        params['ERROR_{}'.format(key)] = str(value)
    LOGGER.info('Error on processing request "{}"'.format(dumps(error)),
                extra=context_unpack(request, {'MESSAGE_ID': 'error_handler'}, params))
    request.response.status = status
    request.response.content_type = 'application/json'
    return {
        "status": "error",
        "errors": [error]
    }


def add_logging_context(event):
    request = event.request
    params = {
        'API_VERSION': VERSION,
        'TAGS': 'python,api',
        'USER': str(request.authenticated_userid or ''),
        #'ROLE': str(request.authenticated_role),
        'CURRENT_URL': request.url,
        'CURRENT_PATH': request.path_info,
        'REMOTE_ADDR': request.remote_addr or '',
        'USER_AGENT': request.user_agent or '',
        'REQUEST_METHOD': request.method,
        'TIMESTAMP': get_now().isoformat(),
        'REQUEST_ID': request.environ.get('REQUEST_ID', ''),
        'CLIENT_REQUEST_ID': request.headers.get('X-Client-Request-ID', ''),
    }

    request.logging_context = params


def request_params(request):
    try:
        params = NestedMultiDict(request.GET, request.POST)
    except UnicodeDecodeError:
        response = exception_response(422)
        response.body = dumps(error_handler(request, response.code,
                                            {"location": "body",
                                             "name": "data",
                                             "description": "could not decode params"}))
        response.content_type = 'application/json'
        raise response
    except Exception as e:
        response = exception_response(422)
        response.body = dumps(error_handler(request, response.code,
                                            {"location": "body",
                                             "name": str(e.__class__.__name__),
                                             "description": str(e)}))
        response.content_type = 'application/json'
        raise response
    return params


def set_logging_context(event):
    request = event.request
    params = dict()
    params['ROLE'] = str(request.authenticated_role)
    if request.params:
        params['PARAMS'] = str(dict(request.params))
    update_logging_context(request, params)


def set_renderer(event):
    request = event.request
    try:
        json = request.json_body
    except ValueError:
        json = {}
    pretty = isinstance(json, dict) and json.get('options', {}).get('pretty') or request.params.get('opt_pretty')
    accept = request.headers.get('Accept')
    jsonp = request.params.get('opt_jsonp')
    if jsonp and pretty:
        request.override_renderer = 'prettyjsonp'
        return True
    if jsonp:
        request.override_renderer = 'jsonp'
        return True
    if pretty:
        request.override_renderer = 'prettyjson'
        return True
    if accept == 'application/yaml':
        request.override_renderer = 'yaml'
        return True


def auth_check(username, password, request):
    if username in USERS and USERS[username]['password'] == sha512(password).hexdigest():
        return ['g:{}'.format(USERS[username]['group'])]

registration_statuses = {-1: 'cancelled', 1: 'registered',
                         2: 'beingTerminated', 3: 'terminated',
                         4: 'banckruptcyFiled', 5: 'banckruptcyReorganization',
                         6: 'invalidRegistraton'}

registration_status_by_code = lambda x: registration_statuses.get(x, 'other')


def prepare_data(data):
    return {'x_edrInternalId': data.get('id'),
            'registrationStatus': registration_status_by_code(data.get('state')),
            'registrationStatusDetails': data.get('state_text'),
            'identification': {'schema': identification_schema,
                               'id': data.get('code'),
                               'legalName': data.get('name'),
                               'url': data.get('url')}}


def forbidden(request):
    request.response.json_body = error_handler(request, 403, {"location": "url", "name": "permission","description": "Forbidden"})
    return request.response


def prepare_data_details(data):
    founders = data.get('founders', [])
    for founder in founders:
        founder['address'] = get_address(founder)
    additional_activity_kinds = []
    primary_activity_kind = {}
    for activity_kind in data.get('activity_kinds', []):
        if activity_kind.get('is_primary'):
            primary_activity_kind = {'id': activity_kind.get('code'),
                                     'scheme': activityKind_scheme,
                                     'description': activity_kind.get('name')}
        else:
            additional_activity_kinds.append({'id': activity_kind.get('code'),
                                              'scheme': activityKind_scheme,
                                              'description': activity_kind.get('name')})
    result = {'name': data.get('names').get('short') if data.get('names') else None,
              'identification': {'scheme': identification_schema,
                                 'id': data.get('code'),
                                 'legalName': data.get('names').get('display') if data.get('names') else None},
              'founders': founders,
              'management': data.get('management'),
              'activityKind': primary_activity_kind or None,
              'additionalActivityKinds': additional_activity_kinds or None,
              'address': get_address(data)}
    return remove_null_fields(result)


def get_address(data):
    return {'streetAddress': data.get('address').get('address') if data.get('address') else None,
            'postalCode': data.get('address').get('zip') if data.get('address') else None,
            'countryName': data.get('address').get('country') if data.get('address') else None}


def remove_null_fields(data):
    """Remove all keys with 'None' values"""
    for k, v in data.items():
        if isinstance(v, dict):
            remove_null_fields(v)
        if isinstance(v, list):
            for element in v:
                remove_null_fields(element)
        if not data[k]:
            del data[k]
    return data


def read_json(name):
    import os.path
    from json import loads
    curr_dir = os.path.dirname(os.path.realpath(__file__))
    file_path = os.path.join(curr_dir, name)
    with open(file_path) as lang_file:
        data = lang_file.read()
    return loads(data)

TEST_DATA_VERIFY = read_json('test_data_verify.json')
TEST_DATA_DETAILS = read_json('test_data_details.json')


def meta_data(date):
    """return sourceDate in ISO 8601format """
    return {'sourceDate': datetime.strptime(date, '%a, %d %b %Y %H:%M:%S %Z').replace(tzinfo=UTC).isoformat()}