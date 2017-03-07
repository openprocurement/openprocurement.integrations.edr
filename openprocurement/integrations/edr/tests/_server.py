# -*- coding: utf-8 -*-
from bottle import request, response
from simplejson import dumps


def setup_routing(app, func, path='/1.0/subjects', method='GET'):
    """ Setup routs """
    app.routes = []
    app.route(path, method, func)


def response_code():
    code = request.query.code
    if not code.isdigit() or not (len(code) == 10 or len(code) == 8):
        return dumps([])
    response.status = 200
    return dumps([{"code": code,
                   "name": "АКЦІОНЕРНЕ ТОВАРИСТВО КОМЕРЦІЙНИЙ БАНК \"ПРИВАТБАНК\"",
                   "url": "https://zqedr-api.nais.gov.ua/1.0/subjects/2842335",
                   "state": 1,
                   "state_text": "https://zqedr-api.nais.gov.ua/1.0/subjects/2842335",
                   "id": 2842335}])


def response_passport():
    passport = request.query.passport
    if passport.isdigit() and len(passport) == 11:
        response.status = 400
        return dumps({"errors": [{"code": 11, "message": "`passport` parameter has wrong value."}]})
    if passport.isalpha():
        response.status = 400
        return dumps({"errors": [{"code": 11, "message": "`passport` parameter has wrong value."}]})
    response.status = 200
    return dumps([{"code": passport,
                   "name": passport,
                   "url": "https://zqedr-api.nais.gov.ua/1.0/subjects/2842336",
                   "state": 1,
                   "state_text": "https://zqedr-api.nais.gov.ua/1.0/subjects/2842336",
                   "id": 2842336}])


def check_headers():
    if request.headers.get('Authorization') == 'Token':
        response.status = 401
        return dumps({"errors": [{"code": 1, "message": "Authentication credentials were not provided."}]})
    elif request.headers.get('Authorization') == 'Token 123':
        response.status = 401
        return dumps({"errors": [{"code": 2, "message": "Invalid or expired token."}]})


def payment_required():
    response.status = 402
    return dumps({"errors": [{"code": 5, "message": "Paiment required."}]})


def forbidden():
    response.status = 403
    return dumps({"errors": [{"code": 3, "message": "Your account is not permitted to access this resource."}]})


def not_found():
    response.status = 404
    return dumps({"errors": [{"code": 4, "message": "Sorry, that page does not exist."}]})


def not_acceptable():
    response.status = 406
    return dumps({"errors": [{"message": "Message."}]})


def too_many_requests():
    response.status = 429
    response.set_header('Retry-After', 26)
    return dumps({"errors": [{"code": 9, "message": "Request was throttled. Expected available in 26 seconds."}]})


def server_error():
    response.status = 500
    return dumps({"errors": [{"code": 20, "message": "Internal error."}]})


def bad_gateway():
    response.status = 502
    return dumps({"errors": [{"message": "Message."}]})


def two_error_messages():
    response.status = 404
    return dumps({"errors": [{"code": 0, "message": "Message1."}, {"code": 0, "message": "Message2."}]})

