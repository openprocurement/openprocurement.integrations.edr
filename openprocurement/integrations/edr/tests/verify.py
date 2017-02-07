# -*- coding: utf-8 -*-
from openprocurement.integrations.edr.tests.base import BaseWebTest


class TestVerify(BaseWebTest):
    """ Test verify view """

    def test_001(self):
        """ Get info by privat edr """
        response = self.app.get('/verify/14360570')
        self.assertEqual(
            response.json['data'],
            {
                u'code': u'14360570',
                u'name': u'\u0410\u041a\u0426\u0406\u041e\u041d\u0415\u0420\u041d\u0415 \u0422\u041e\u0412\u0410\u0420\u0418\u0421\u0422\u0412\u041e \u041a\u041e\u041c\u0415\u0420\u0426\u0406\u0419\u041d\u0418\u0419 \u0411\u0410\u041d\u041a "\u041f\u0420\u0418\u0412\u0410\u0422\u0411\u0410\u041d\u041a"',
                u'url': u'https://zqedr-api.nais.gov.ua/1.0/subjects/2842335',
                u'state': 1,
                u'state_text': u'https://zqedr-api.nais.gov.ua/1.0/subjects/2842335',
                u'id': 2842335
            })
