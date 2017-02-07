# -*- coding: utf-8 -*-
from bottle import request, response, redirect, static_file
from simplejson import dumps


def setup_routing(app):
    """ Setup routs """
    for rout in routs_dict:
        path, method, func = rout
        app.route(path, method, func)

# Base routes


def verify():
    response.status = 200
    return dumps({"code": "14360570",
                  "name": "АКЦІОНЕРНЕ ТОВАРИСТВО КОМЕРЦІЙНИЙ БАНК \"ПРИВАТБАНК\"",
                  "url": "https://zqedr-api.nais.gov.ua/1.0/subjects/2842335",
                  "state": 1,
                  "state_text": "https://zqedr-api.nais.gov.ua/1.0/subjects/2842335",
                  "id": 2842335})

#### Routs

routs_dict = (
    ("/1.0/subjects", 'GET', verify),
)
