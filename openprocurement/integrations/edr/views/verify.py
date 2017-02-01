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

    @json_view(content_type="application/json", permission='verify')
    def get(self):
        edrpou = self.request.matchdict.get('edrpou')
        try:
            response = self.edr_api.get_subject(edrpou)
        except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectTimeout) as e:
            self.LOGGER.warning('Gateway Timeout Error {}'.format(e.message))
            self.request.errors.add('body', 'data', 'Gateway Timeout Error')
            self.request.errors.status = 403
            return
        if response.status_code == 200:
            self.LOGGER.info('Accept response from EDR service for {} with status 200.'.format(edrpou))
            data = response.json()
            if not data:
                self.LOGGER.warning('Accept empty response from EDR service for {}'.format(edrpou))
                self.request.errors.add('body', 'data', 'EDRPOU not found')
                self.request.errors.status = 403
                return
            self.LOGGER.warning('Return data from EDR service for {}'.format(edrpou))
            return {'data': data}
        elif response.status_code == 429:
            retry_after = response.headers.get('Retry-After')
            self.LOGGER.error('Too many requests (response status 429) while connecting to EDR service. EDRPOU {}. '
                              'Retry after {}'.format(edrpou, retry_after))
            self.request.errors.add('body', 'data', 'Retry request after {}'.format(retry_after))
            self.request.errors.status = 403
            return
        elif response.status_code == 502:
            self.LOGGER.error('Service is disabled or upgrade, response status 502. EDRPOU {}.'.format(edrpou))
            self.request.errors.add('body', 'data', 'Service is disabled or upgrade.')
            self.request.errors.status = 403
            return
        else:
            messages = [error['message'] for error in response.json()['errors']]
            self.LOGGER.error('Accept error while connecting to EDR service. Response status {}. Message {}. '
                              'EDRPOU {}.'.format(response.status_code, messages, edrpou))
            self.request.errors.add('body', 'data', 'Error while processing request. Message: {}'.format(messages))
            self.request.errors.status = 403
            return
            #TODO TIMEOUT


