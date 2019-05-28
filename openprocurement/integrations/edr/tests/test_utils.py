# -*- coding: utf-8 -*-
from mock import MagicMock
from openprocurement.integrations.edr.tests.base import BaseWebTest
from openprocurement.integrations.edr.utils import Db
from openprocurement.integrations.edr.auth import authenticated_role

config = {
    "cache_host": "127.0.0.1",
    "cache_port": "16379",
    "cache_db_name": 0
}


class TestUtils(BaseWebTest):

    def test_db_init(self):
        db = Db(config)
        self.assertEqual(db._backend, "redis")
        self.assertEqual(db._db_name, 0)
        self.assertEqual(db._port, "16379")
        self.assertEqual(db._host, "127.0.0.1")
        del db

    def test_db_get(self):
        db = Db(config)
        self.assertIsNone(db.get("111"))
        db.put("111", "test data")
        self.assertEqual(db.get("111"), "test data")

    def test_db_set(self):
        db = Db(config)
        db.put("111", "test data")
        self.assertEqual(db.get("111"), "test data")

    def test_db_has(self):
        db = Db(config)
        self.assertFalse(db.has("111"))
        db.put("111", "test data")
        self.assertTrue(db.has("111"))

    def test_authenticated_role(self):
        request = MagicMock(effective_principals=['g:robots', 'a', 'b'])
        self.assertEqual(authenticated_role(request), 'robots')
