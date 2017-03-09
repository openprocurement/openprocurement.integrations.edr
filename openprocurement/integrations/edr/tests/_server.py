# -*- coding: utf-8 -*-
import requests

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


def response_details():
    response.status = 200
    return dumps({
      "id": 2842335,
      "state": 1,
      "state_text": "зареєстровано",
      "code": "14360570",
      "names": {
        "short": "ПАТ КБ \"ПРИВАТБАНК\"",
        "name": "КОМЕРЦІЙНИЙ БАНК \"ПРИВАТБАНК\"",
        "short_en": "PJSC CB \"PRIVATBANK\"",
        "include_olf": 1,
        "name_en": "PUBLIC JOINT-STOCK COMPANY COMMERCIAL BANK \"PRIVATBANK\"",
        "display": "АКЦІОНЕРНЕ ТОВАРИСТВО КОМЕРЦІЙНИЙ БАНК \"ПРИВАТБАНК\""
      },
      "olf_code": "230",
      "olf_name": "АКЦІОНЕРНЕ ТОВАРИСТВО",
      "founding_document": None,
      "executive_power": None,
      "object_name": "Реєстраційна служба Дніпропетровського міського управління юстиції Дніпропетровської області",
      "founders": [
        {
          "capital": 18100740000,
          "role_text": "засновник",
          "name": "АКЦІОНЕРИ - ЮРИДИЧНІ ТА ФІЗИЧНІ ОСОБИ, ЩО ВОЛОДІЮТЬ У СУКУПНОСТІ 64645500 ПРОСТИМИ ІМЕННИМИ АКЦІЯМИ НА СУ40000  ГРИВЕНЬ",
          "address": None,
          "role": 4
        }
      ],
      "management": "ЗАГАЛЬНІ ЗБОРИ",
      "heads": [
        {
          "appointment_date": None,
          "role_text": "підписант",
          "last_name": "ПІКУШ",
          "first_middle_name": "ЮРІЙ ПЕТРОВИЧ",
          "restriction": "Повноваження згідно положень статуту",
          "role": 2
        },
        {
          "appointment_date": None,
          "role_text": "підписант",
          "last_name": "НОВІКОВ",
          "first_middle_name": "ТИМУР ЮРІЙОВИЧ",
          "restriction": "Повноваження згідно положень статуту",
          "role": 2
        },
        {
          "appointment_date": None,
          "role_text": "підписант",
          "last_name": "ЯЦЕНКО",
          "first_middle_name": "ВОЛОДИМИР АНАТОЛІЙОВИЧ",
          "restriction": "Повноваження згідно положень статуту",
          "role": 2
        },
        {
          "appointment_date": None,
          "role_text": "керівник",
          "last_name": "ДУБІЛЕТ",
          "first_middle_name": "ОЛЕКСАНДР ВАЛЕРІЙОВИЧ",
          "restriction": "Повноваження згідно положень статуту",
          "role": 3
        },
        {
          "appointment_date": None,
          "role_text": "підписант",
          "last_name": "ГУР'ЄВА",
          "first_middle_name": "ТЕТЯНА МИХАЙЛІВНА",
          "restriction": "Повноваження згідно положень статуту",
          "role": 2
        },
        {
          "appointment_date": None,
          "role_text": "підписант",
          "last_name": "ШМАЛЬЧЕНКО",
          "first_middle_name": "ЛЮДМИЛА ОЛЕКСАНДРІВНА",
          "restriction": "Повноваження згідно положень статуту",
          "role": 2
        },
        {
          "appointment_date": None,
          "role_text": "підписант",
          "last_name": "КАНДАУРОВ",
          "first_middle_name": "ЮРІЙ ВАСИЛЬОВИЧ",
          "restriction": "Повноваження згідно положень статуту",
          "role": 2
        },
        {
          "appointment_date": None,
          "role_text": "підписант",
          "last_name": "ЧМОНА",
          "first_middle_name": "ЛЮБОВ ІВАНІВНА",
          "restriction": "Повноваження згідно положень статуту",
          "role": 2
        },
        {
          "appointment_date": None,
          "role_text": "підписант",
          "last_name": "ГОРОХОВСЬКИЙ",
          "first_middle_name": "ОЛЕГ ВОЛОДИМИРОВИЧ",
          "restriction": "Повноваження згідно положень статуту",
          "role": 2
        },
        {
          "appointment_date": None,
          "role_text": "підписант",
          "last_name": "ЗАВОРОТНИЙ",
          "first_middle_name": "ВОЛОДИМИР ГРИГОРОВИЧ",
          "restriction": "Повноваження згідно положень статуту",
          "role": 2
        },
        {
          "appointment_date": "2014-01-23",
          "role_text": "підписант",
          "last_name": "НЕГИНСЬКИЙ",
          "first_middle_name": "РОМАН МАРКОВИЧ",
          "restriction": "",
          "role": 2
        },
        {
          "appointment_date": "2010-01-01",
          "role_text": "підписант",
          "last_name": "ЄРИКАЛОВА",
          "first_middle_name": "ІРИНА ОЛЕКСІЇВНА",
          "restriction": "",
          "role": 2
        },
        {
          "appointment_date": "2009-08-18",
          "role_text": "підписант",
          "last_name": "ВІТЯЗЬ",
          "first_middle_name": "ОЛЕКСАНДР ПАВЛОВИЧ",
          "restriction": "ПОВНОВАЖЕННЯ ЗГІДНО ПОЛОЖЕНЬ СТАТУТУ",
          "role": 2
        },
        {
          "appointment_date": "2009-05-27",
          "role_text": "підписант",
          "last_name": "КРИЖАНОВСЬКИЙ",
          "first_middle_name": "СТАНІСЛАВ ВІКЕНТІЙОВИЧ",
          "restriction": "ПОВНОВАЖЕННЯ ЗГІДНО ПОЛОЖЕНЬ СТАТУТУ",
          "role": 2
        }
      ],
      "managing_paper": None,
      "is_modal_statute": False,
      "activity_kinds": [
        {
          "name": "Інші види грошового посередництва",
          "is_primary": True,
          "code": "64.19"
        },
        {
          "name": "Інші види кредитування",
          "is_primary": False,
          "code": "64.92"
        },
        {
          "name": "Надання інших фінансових послуг (крім страхування та пенсійного забезпечення), н. в. і. у.",
          "is_primary": False,
          "code": "64.99"
        },
        {
          "name": "Управління фінансовими ринками",
          "is_primary": False,
          "code": "66.11"
        },
        {
          "name": "Посередництво за договорами по цінних паперах або товарах",
          "is_primary": False,
          "code": "66.12"
        },
        {
          "name": "Інша допоміжна діяльність у сфері фінансових послуг, крім страхування та пенсійного забезпечення",
          "is_primary": False,
          "code": "66.19"
        }
      ],
      "branches": [
        {
          "type": 122,
          "name": "КІПРСЬКА ФІЛІЯ ПУБЛІЧНОГО АКЦІОНЕРНОГО ТОВАРИСТВА КОМЕРЦІЙНОГО БАНКУ \"ПРИВАТБАНК\"",
          "address": {
            "country": "КІПР",
            "address": "1055, КАЛІПОЛЕОС, 3, 3-Й ПОВЕРХ, М.НІКОСІЯ, КІПР.",
            "zip": ""
          },
          "code": "",
          "type_text": "Філія (інший відокремлений підрозділ)"
        }
      ],
      "address": {
        "country": "УКРАЇНА",
        "address": "Дніпропетровська обл., місто Дніпропетровськ, Жовтневий район ВУЛИЦЯ НАБЕРЕЖНА ПЕРЕМОГИ буд. 50",
        "zip": "49094"
      },
      "registraion": {
        "record_date": "2005-01-27",
        "is_transformation": False,
        "is_division": False,
        "date": "1992-03-19",
        "is_merge": False,
        "record_number": "12241200000006727",
        "is_separation": False
      },
      "bankruptcy": None,
      "termination": None,
      "termination_cancel": None,
      "assignees": [],
      "predecessors": [],
      "registrations": [
        {
          "start_date": "1992-10-01",
          "name": "ГОЛОВНЕ УПРАВЛІННЯ РЕГІОНАЛЬНОЇ СТАТИСТИКИ",
          "start_num": None,
          "end_num": None,
          "type": "",
          "code": "21680000",
          "end_date": None,
          "description": None
        },
        {
          "start_date": "1994-12-22",
          "name": "СДПI У М.ДНIПРОПЕТРОВСЬКУ МГУМ",
          "start_num": "9",
          "end_num": None,
          "type": "4002",
          "code": "38752875",
          "end_date": None,
          "description": "дані про взяття на облік як платника податків"
        },
        {
          "start_date": "2011-03-24",
          "name": "СДПI У М.ДНIПРОПЕТРОВСЬКУ МГУМ",
          "start_num": "04030339603",
          "end_num": None,
          "type": "4001",
          "code": "38752875",
          "end_date": None,
          "description": "дані про взяття на облік як платника єдиного внеску"
        }
      ],
      "primary_activity_kind": {
        "name": "Інші види грошового посередництва",
        "reg_number": "04030339603",
        "code": "64.19",
        "class": "5"
      },
      "prev_registration_end_term": None,
      "open_enforcements": [
        "2015-05-27",
        "2015-05-27",
        "2015-09-07",
        "2015-08-04",
        "2015-09-08",
        "2015-08-04",
        "2015-05-11",
        "2015-09-22",
        "2015-09-21",
        "2015-01-28",
        "2015-07-17",
        "2015-09-01",
        "2015-11-12",
        "2015-10-12",
        "2015-10-26",
        "2015-10-29",
        "2015-10-23",
        "2015-05-27",
        "2015-07-02",
        "2013-09-09",
        "2013-09-06",
        "2015-09-23",
        "2015-09-24",
        "2015-09-18",
        "2015-10-20",
        "2015-10-20",
        "2015-11-10",
        "2015-10-30",
        "2015-09-30",
        "2015-10-30",
        "2015-11-10",
        "2015-11-12",
        "2015-10-06",
        "2015-10-26",
        "2015-05-21",
        "2015-10-30",
        "2015-10-12",
        "2015-11-12",
        "2009-10-29",
        "2011-01-14",
        "2010-05-21",
        "2015-10-29",
        "2015-11-10",
        "2015-04-03",
        "2015-07-28",
        "2015-09-24",
        "2015-05-27",
        "2012-11-29",
        "2015-09-24",
        "2015-10-09",
        "2015-05-27",
        "2015-10-30",
        "2015-07-17",
        "2015-09-22",
        "2015-09-16",
        "2014-09-04",
        "2015-03-12",
        "2015-07-07",
        "2015-11-12",
        "2015-10-20",
        "2015-09-16",
        "2015-11-10",
        "2015-11-11",
        "2015-08-27",
        "2015-03-27",
        "2015-06-26",
        "2015-05-28",
        "2014-08-18",
        "2015-11-12",
        "2013-02-25",
        "2015-10-20",
        "2015-09-10",
        "2015-11-06",
        "2015-10-30",
        "2015-10-30",
        "2015-10-30",
        "2015-10-28",
        "2015-10-26",
        "2015-10-09",
        "2015-11-12",
        "2015-10-23",
        "2015-10-26",
        "2015-10-20",
        "2015-10-30",
        "2011-07-08",
        "2015-09-21",
        "2015-10-12",
        "2015-08-14",
        "2015-10-23",
        "2015-10-23",
        "2015-11-12",
        "2015-09-22",
        "2015-05-27",
        "2015-08-31",
        "2015-09-08",
        "2015-10-01",
        "2015-08-14",
        "2015-10-26",
        "2015-04-07",
        "2015-08-20",
        "2015-10-09",
        "2015-07-28",
        "2015-10-12",
        "2015-11-12",
        "2015-09-23",
        "2015-09-23",
        "2015-11-10",
        "2015-05-27",
        "2015-02-26",
        "2015-05-21",
        "2015-05-27",
        "2015-09-21",
        "2015-11-12",
        "2015-11-13",
        "2015-09-07",
        "2015-10-12",
        "2015-10-30",
        "2015-10-30",
        "2015-10-09",
        "2015-10-08",
        "2015-10-01",
        "2015-10-12",
        "2015-10-09",
        "2015-06-16",
        "2015-10-23",
        "2015-11-10",
        "2015-10-30",
        "2015-10-07",
        "2015-11-05",
        "2015-10-12",
        "2015-04-07",
        "2015-05-27",
        "2014-01-22",
        "2015-10-20",
        "2015-11-12",
        "2015-10-29",
        "2015-10-09",
        "2012-09-25",
        "2010-11-10",
        "2015-10-01",
        "2015-08-04",
        "2015-09-22",
        "2015-07-28",
        "2014-11-19",
        "2015-10-12",
        "2015-10-30",
        "2015-09-23",
        "2015-10-30",
        "2015-11-12",
        "2015-10-12",
        "2015-10-12",
        "2015-10-20",
        "2015-07-02",
        "2015-11-11",
        "2015-10-16",
        "2015-10-23",
        "2015-10-23",
        "2015-10-23",
        "2015-10-23",
        "2015-10-28",
        "2015-10-23",
        "2015-07-06",
        "2015-10-12",
        "2015-05-26",
        "2015-09-07",
        "2015-10-20",
        "2015-10-26",
        "2015-10-12",
        "2015-10-27",
        "2015-10-30",
        "2015-10-30",
        "2015-10-20",
        "2015-10-30",
        "2015-09-22",
        "2015-11-12",
        "2015-10-30",
        "2014-11-21",
        "2015-07-16",
        "2015-05-27",
        "2015-05-27",
        "2015-02-09",
        "2015-03-12",
        "2015-03-04",
        "2015-06-03",
        "2011-08-22",
        "2015-04-30",
        "2015-08-14",
        "2014-09-22",
        "2014-01-20",
        "2015-09-21",
        "2015-08-14",
        "2015-08-31",
        "2015-07-17",
        "2015-07-14",
        "2015-08-14",
        "2015-07-28",
        "2015-11-12",
        "2015-11-12",
        "2015-10-30",
        "2015-10-12",
        "2015-11-12",
        "2015-11-12",
        "2015-10-30",
        "2015-10-09",
        "2015-10-12",
        "2015-10-28",
        "2015-10-12",
        "2015-11-12",
        "2015-09-18",
        "2015-03-18",
        "2014-03-18",
        "2014-01-29",
        "2015-07-16",
        "2015-09-10",
        "2015-10-30",
        "2015-10-12",
        "2015-06-11",
        "2015-09-21",
        "2015-06-11",
        "2015-10-28",
        "2015-10-12",
        "2015-03-27",
        "2015-05-27",
        "2015-03-26",
        "2015-11-06",
        "2015-06-16",
        "2015-10-23",
        "2015-11-10",
        "2015-10-26",
        "2015-10-26",
        "2015-10-23",
        "2015-10-23",
        "2015-10-28",
        "2015-10-28",
        "2015-02-26",
        "2014-09-03",
        "2014-03-18",
        "2015-11-12",
        "2015-10-26",
        "2015-11-12",
        "2015-05-27",
        "2015-10-09",
        "2015-10-01",
        "2015-09-23",
        "2015-07-13"
      ],
      "contacts": {
        "tel": [
          "+380567165119",
          "+380567896021"
        ],
        "web_page": "www.privatbank.ua",
        "fax": "",
        "email": ""
      }
    })


def too_many_requests_details():
    response.status = 429
    response.set_header('Retry-After', 26)
    return dumps({"errors": [{"code": 9, "message": "Request was throttled. Expected available in 26 seconds."}]})


def bad_gateway_details():
    response.status = 502
    return dumps({"errors": [{"message": "Message."}]})
