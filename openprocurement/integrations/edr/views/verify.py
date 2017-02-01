# -*- coding: utf-8 -*-
from openprocurement.api.utils import (
    json_view,
)
from openprocurement.integrations.edr.utils import opresource, APIResource


@opresource(name='Verify customer',
            path='/verify/{edrpou}',
            description="Verify customer by edr code ")
class VerifyUResource(APIResource):
    """ Verify customer """

    @json_view(content_type="application/json", permission='verify')
    def get(self):
        response = self.edr_api.get_subject(self.request.matchdict.get('edrpou'))
        if response.status_code == 200:
            data = response.json()
            if not data:
                self.request.errors.add('body', 'data', 'EDRPOU not found')
                self.request.errors.status = 403
                return
            return {'data': data}
        elif response.status_code == 400:
            messages = [error['message'] for error in response.json()['errors']]
            self.request.errors.add('body', 'data', 'Bad request. Message: {}'.format(messages))
            self.request.errors.status = 403
            return
        #TODO all another errors realize

