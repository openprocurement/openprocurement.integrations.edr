import openprocurement.integrations.edr.views.health
from openprocurement.integrations.edr.tests.base import BaseWebTest


class TestHealth(BaseWebTest):
    """ Test health view"""

    def test_health(self):
        openprocurement.integrations.edr.views.health.SANDBOX_MODE = False
        response = self.app.get('/health', headers={'sandbox-mode': 'True'}, expect_errors=True)
        self.assertEqual(response.status, "200 OK")
        self.assertEqual(response.content_type, "application/json")
        openprocurement.integrations.edr.views.health.SANDBOX_MODE = False
        response = self.app.get('/health', headers={'sandbox-mode': 'False'}, expect_errors=True)
        self.assertEqual(response.status, "200 OK")
        self.assertEqual(response.content_type, "application/json")
        openprocurement.integrations.edr.views.health.SANDBOX_MODE = True
        response = self.app.get('/health', headers={'sandbox-mode': 'True'}, expect_errors=True)
        self.assertEqual(response.status, "200 OK")
        self.assertEqual(response.content_type, "application/json")
        openprocurement.integrations.edr.views.health.SANDBOX_MODE = True
        response = self.app.get('/health', headers={'sandbox-mode': 'False'}, expect_errors=True)
        self.assertEqual(response.status, "400 Sandbox modes mismatch between proxy and bot")
        self.assertEqual(response.content_type, "application/json")

