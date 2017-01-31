# -*- coding: utf-8 -*-
from openprocurement.api.utils import (
    json_view,
)
from openprocurement.integrations.edr.utils import opresource, APIResource


@opresource(name='Verify customer',
            path='/verify/{edrpo}',
            description="Verify customer by edr code ")
class VerifyUResource(APIResource):
    """ Verify customer """

    @json_view(content_type="application/json", permission='verify')
    def get(self):
        return {
            'data': 'You are awesome {} {}'.format(
                self.request.matchdict.get('edrpo'),
                self.edr_api)
        }
