# -*- coding: utf-8 -*-
import os
from functools import partial
from logging import getLogger
from json import dumps
from cornice.util import json_error
from pkg_resources import get_distribution
from cornice.resource import resource, view
from webob.multidict import NestedMultiDict
from datetime import datetime
from pytz import timezone

from openprocurement.integrations.edr.traversal import factory


PKG = get_distribution(__package__)
LOGGER = getLogger(PKG.project_name)
VERSION = '{}.{}'.format(int(PKG.parsed_version[0]), int(PKG.parsed_version[1]) if PKG.parsed_version[1].isdigit() else 0)
ROUTE_PREFIX = '/api/{}'.format(VERSION)
json_view = partial(view, renderer='json')
TZ = timezone(os.environ['TZ'] if 'TZ' in os.environ else 'Europe/Kiev')


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


def error_handler(errors, request_params=True):
    params = {'ERROR_STATUS': errors.status}
    if request_params:
        params['ROLE'] = str(errors.request.authenticated_role)
        if errors.request.params:
            params['PARAMS'] = str(dict(errors.request.params))
    if errors.request.matchdict:
        for x, j in errors.request.matchdict.items():
            params[x.upper()] = j
    if 'tender' in errors.request.validated:
        params['TENDER_REV'] = errors.request.validated['tender'].rev
        params['TENDERID'] = errors.request.validated['tender'].tenderID
        params['TENDER_STATUS'] = errors.request.validated['tender'].status
    LOGGER.info('Error on processing request "{}"'.format(dumps(errors, indent=4)),
                extra=context_unpack(errors.request, {'MESSAGE_ID': 'error_handler'}, params))
    return json_error(errors)


def forbidden(request):
    request.errors.add('url', 'permission', 'Forbidden')
    request.errors.status = 403
    return error_handler(request.errors)


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
        request.errors.add('body', 'data', 'could not decode params')
        request.errors.status = 422
        raise error_handler(request.errors, False)
    except Exception as e:
        request.errors.add('body', str(e.__class__.__name__), str(e))
        request.errors.status = 422
        raise error_handler(request.errors, False)
    return params


def set_logging_context(event):
    request = event.request

    params = {}
    params['ROLE'] = str(request.authenticated_role)
    if request.params:
        params['PARAMS'] = str(dict(request.params))
    if request.matchdict:
        for x, j in request.matchdict.items():
            params[x.upper()] = j
    if 'tender' in request.validated:
        params['TENDER_REV'] = request.validated['tender'].rev
        params['TENDERID'] = request.validated['tender'].tenderID
        params['TENDER_STATUS'] = request.validated['tender'].status
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


def fix_url(item, app_url):
    if isinstance(item, list):
        [
            fix_url(i, app_url)
            for i in item
            if isinstance(i, dict) or isinstance(i, list)
        ]
    elif isinstance(item, dict):
        if "format" in item and "url" in item and '?download=' in item['url']:
            path = item["url"] if item["url"].startswith('/') else '/' + '/'.join(item['url'].split('/')[5:])
            item["url"] = app_url + ROUTE_PREFIX + path
            return
        [
            fix_url(item[i], app_url)
            for i in item
            if isinstance(item[i], dict) or isinstance(item[i], list)
        ]


def beforerender(event):
    if event.rendering_val and isinstance(event.rendering_val, dict) and 'data' in event.rendering_val:
        fix_url(event.rendering_val['data'], event['request'].application_url)


opresource = partial(resource, error_handler=error_handler, factory=factory)


class APIResource(object):

    def __init__(self, request, context):
        self.context = context
        self.request = request
        self.server_id = request.registry.server_id
        self.edr_api = request.registry.edr_client
        self.LOGGER = getLogger(type(self).__module__)
