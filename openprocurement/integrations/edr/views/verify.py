# -*- coding: utf-8 -*-
import requests
from pyramid.view import view_config
from logging import getLogger
from openprocurement.integrations.edr.utils import (error_handler, get_sandbox_data, db_key, cached_details,
                                                    cached_verify, form_edr_response, default_error_status, EDRDetails)

LOGGER = getLogger(__name__)


@view_config(route_name='verify', renderer='json', request_method='GET', permission='verify')
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
    if role == "robots":
        res = cached_details(request, details.code)
        if res:
            return res
    elif request.registry.cache_db.has(db_key(details.code, "verify")):
        return cached_verify(request, details.code)
    LOGGER.info("Code {} was not found in cache at {}".format(
        details.code, db_key(details.code, "details" if role == "robots" else "verify")))
    data = get_sandbox_data(request, code)  # return test data if SANDBOX_MODE=True and data exists for given code
    if data:
        return data
    try:
        response = request.registry.edr_client.get_subject(**details._asdict())
    except (requests.exceptions.ReadTimeout,
            requests.exceptions.ConnectTimeout):
        return error_handler(request, default_error_status, {"location": "url", "name": "id",
                                                             "description": [{u'message': u'Gateway Timeout Error'}]})
    return form_edr_response(request, response, details.code)
