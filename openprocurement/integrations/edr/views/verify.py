# -*- coding: utf-8 -*-
import requests
from openprocurement.api.utils import (
    json_view,
)
from openprocurement.integrations.edr.utils import opresource, APIResource


@opresource(name='Verify customer',
            path='/verify/{edrpou}',
            description="Verify customer by edr code ")
class VerifyUResource(APIResource):
    """ Verify customer """

    def handle_error(self, message):
        self.request.errors.add('body', 'data', message)
        self.request.errors.status = 403

    @json_view(permission='verify')
    def get(self):
        edrpou = self.request.matchdict.get('edrpou')
        try:
            response = self.edr_api.get_subject(edrpou)
        except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectTimeout):
            self.handle_error('Gateway Timeout Error')
            return
        if response.status_code == 200:
            data = response.json()
            if not data:
                self.LOGGER.warning('Accept empty response from EDR service for {}'.format(edrpou))
                self.handle_error('EDRPOU not found')
                return
            self.LOGGER.info('Return data from EDR service for {}'.format(edrpou))
            return {'data': data}
        elif response.status_code == 429:
            self.handle_error('Retry request after {}'.format(response.headers.get('Retry-After')))
            return
        elif response.status_code == 502:
            self.handle_error('Service is disabled or upgrade.')
            return
        else:
            self.handle_error([error['message'] for error in response.json()['errors']])
            return
