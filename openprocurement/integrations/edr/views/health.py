from pyramid.view import view_config
from openprocurement.integrations.edr.utils import SANDBOX_MODE


@view_config(route_name='health', renderer='json', request_method='GET')
def health(request):
    """:return status of proxy server"""
    if SANDBOX_MODE and request.headers.get("sandbox-mode", str(SANDBOX_MODE)).lower() != 'true':
        request.response.status = "400 Sandbox modes mismatch between proxy and bot"
    return ''
