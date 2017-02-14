# -*- coding: utf-8 -*-
from cornice.resource import resource
from functools import partial
from logging import getLogger

from openprocurement.api.utils import error_handler
from openprocurement.integrations.edr.traversal import factory


opresource = partial(resource, error_handler=error_handler, factory=factory)


class APIResource(object):

    def __init__(self, request, context):
        self.context = context
        self.request = request
        self.server_id = request.registry.server_id
        self.edr_api = request.registry.edr_client
        self.LOGGER = getLogger(type(self).__module__)
