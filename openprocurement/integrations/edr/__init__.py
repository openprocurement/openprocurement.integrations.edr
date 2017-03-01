# -*- coding: utf-8 -*-
"""Main entry point
"""
if 'test' not in __import__('sys').argv[0]:
    import gevent.monkey
    gevent.monkey.patch_all()

from logging import getLogger
from openprocurement.integrations.edr.client import EdrClient


LOGGER = getLogger("{}.init".format(__name__))
SECURITY = {u'admins': {u'names': [], u'roles': ['_admin']}, u'members': {u'names': [], u'roles': ['_admin']}}


def main(global_config, **settings):
    from openprocurement.integrations.edr.auth import (
        AuthenticationPolicy, authenticated_role, check_accreditation
    )
    from openprocurement.integrations.edr.utils import (
        forbidden, add_logging_context, set_logging_context,
        request_params, set_renderer, beforerender, ROUTE_PREFIX
    )
    from pyramid.authorization import (
        ACLAuthorizationPolicy as AuthorizationPolicy
    )
    from pyramid.config import Configurator
    from pyramid.events import NewRequest, BeforeRender, ContextFound
    from pyramid.renderers import JSON, JSONP
    from pyramid.settings import asbool

    LOGGER.info('Start edr api')
    config = Configurator(
        autocommit=True,
        settings=settings,
        authentication_policy=AuthenticationPolicy(settings['auth.file'], __name__),
        authorization_policy=AuthorizationPolicy(),
        route_prefix=ROUTE_PREFIX,
    )
    config.include('pyramid_exclog')
    config.include("cornice")
    config.add_forbidden_view(forbidden)
    config.add_request_method(request_params, 'params', reify=True)
    config.add_request_method(authenticated_role, reify=True)
    config.add_request_method(check_accreditation)
    config.add_renderer('prettyjson', JSON(indent=4))
    config.add_renderer('jsonp', JSONP(param_name='opt_jsonp'))
    config.add_renderer('prettyjsonp', JSONP(indent=4, param_name='opt_jsonp'))
    config.add_renderer('yaml', 'openprocurement.integrations.edr.renderers.YAMLRenderer')
    config.add_subscriber(add_logging_context, NewRequest)
    config.add_subscriber(set_logging_context, ContextFound)
    config.add_subscriber(set_renderer, NewRequest)
    config.add_subscriber(beforerender, BeforeRender)
    # config.scan("openprocurement.api.views.spore")  # TODO: UNCOMMENT IT
    # config.scan("openprocurement.api.views.health")

    config.registry.server_id = settings.get('id', '')
    config.registry.health_threshold = float(settings.get('health_threshold', 99))
    config.registry.update_after = asbool(settings.get('update_after', True))

    # Init edr connection
    config.registry.edr_client = EdrClient(settings.get('edr_api_server'),
                                           settings.get('edr_api_token'),
                                           float(settings.get('edr_timeout')),
                                           int(settings.get('edr_api_port')))

    # Include views
    config.scan("openprocurement.integrations.edr.views")

    return config.make_wsgi_app()
