# -*- coding: utf-8 -*-
import json

import requests
from collections import namedtuple
from pyramid.view import view_config
from logging import getLogger
from openprocurement.integrations.edr.utils import (prepare_data_details, prepare_data, error_handler, meta_data,
                                                    get_sandbox_data, db_key, error_message_404)

LOGGER = getLogger(__name__)
EDRDetails = namedtuple("EDRDetails", ['param', 'code'])
default_error_status = 403

# TODO: 1) Redo cache details inner -> details; - DONE
# TODO: 2) remove em404 and lifetime consts - DONE
# TODO: 3) Every first one should be cached
# TODO: 4) roles -> ref type when in cache - DONE
# TODO: 5) redo tests accordingly - DONE
# TODO: 6) TTL for negative and positive should differ


def handle_error(request, response):
    if response.headers['Content-Type'] != 'application/json':
        return error_handler(request, default_error_status, {"location": "request", "name": "ip",
                                                             "description": [{u'message': u'Forbidden'}]})
    if response.status_code == 429:
        seconds_to_wait = response.headers.get('Retry-After')
        request.response.headers['Retry-After'] = seconds_to_wait
        return error_handler(request, 429, {"location": "body", "name": "data",
                                            "description": [{u'message': u'Retry request after {} seconds.'.format(seconds_to_wait)}]})
    elif response.status_code == 502:
        return error_handler(request, default_error_status, {"location": "body", "name": "data",
                                                             "description": [{u'message': u'Service is disabled or upgrade.'}]})
    return error_handler(request, default_error_status, {"location": "body", "name": "data",
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
            return error_handler(request, default_error_status,
                                 {"location": "url", "name": "id",
                                  "description": [{u'message': u'Wrong name of the GET parameter'}]})
        details = EDRDetails('passport', passport)
    edr_data_type = "details" if role == "robots" else "verify"
    if role == "robots":
        if request.registry.cache_db.has(db_key(details.code, "details")):
            LOGGER.info("Code {} was found in cache at {}".format(details.code, db_key(details.code, "details")))
            redis_data = json.loads(request.registry.cache_db.get(db_key(details.code, "details")))
            return redis_data
        elif request.registry.cache_db.has(db_key(details.code, "verify")):
            redis_data = json.loads(request.registry.cache_db.get(db_key(details.code, "verify")))
            if redis_data.get("errors"):
                return error_handler(request, 404, redis_data["errors"][0])
            data_details = user_details(request, [obj['x_edrInternalId'] for obj in redis_data['data']])
            request.registry.cache_db.put(db_key(details.code, "details"), json.dumps(data_details),
                                          request.registry.time_to_live)
            return data_details
    elif request.registry.cache_db.has(db_key(details.code, "verify")):
        LOGGER.info("Code {} was found in cache at {}".format(details.code, db_key(details.code, "verify")))
        redis_data = json.loads(request.registry.cache_db.get(db_key(details.code, "verify")))
        if redis_data.get("errors"):
            return error_handler(request, 404, redis_data["errors"][0])
        return redis_data
    LOGGER.debug("Code {} was not found in cache at {}".format(details.code, db_key(details.code, edr_data_type)))
    data = get_sandbox_data(request, role, code)  # return test data if SANDBOX_MODE=True and data exists for given code
    if data:
        return data

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
            res = error_handler(request, 404, {"location": "body", "name": "data",
                                               "description": [{u"error": error_message_404,
                                                                u'meta': {"sourceDate": meta_data(
                                                                     response.headers['Date'])}}]})
            request.registry.cache_db.put(db_key(details.code, "verify"), json.dumps(res),
                                          request.registry.time_to_live)
            return res
        res = {'data': [prepare_data(d) for d in data], 'meta': {'sourceDate': meta_data(response.headers['Date'])}}
        request.registry.cache_db.put(db_key(details.code, "verify"), json.dumps(res), request.registry.time_to_live)
        if role == 'robots':  # get details for edr-bot
            data_details = user_details(request, [obj['id'] for obj in data])
            request.registry.cache_db.put(db_key(details.code, "details"), json.dumps(data_details),
                                          request.registry.time_to_live)
            return data_details
        return res
    else:
        return handle_error(request, response)


def user_details(request, internal_ids):
    """Composes array of detailed reference files"""
    data = []
    details_source_date = []
    for internal_id in internal_ids:
        try:
            response = request.registry.edr_client.get_subject_details(internal_id)
        except (requests.exceptions.ReadTimeout,
                requests.exceptions.ConnectTimeout):
            return error_handler(request, default_error_status, {"location": "url", "name": "id",
                                                                 "description": [{u'message': u'Gateway Timeout Error'}]})
        if response.status_code != 200:
            return handle_error(request, response)
        else:
            LOGGER.info('Return detailed data from EDR service for {}'.format(internal_id))
            data.append(prepare_data_details(response.json()))
            details_source_date.append(meta_data(response.headers['Date']))
    return {"data": data, "meta": {"sourceDate": details_source_date[-1], "detailsSourceDate": details_source_date}}
