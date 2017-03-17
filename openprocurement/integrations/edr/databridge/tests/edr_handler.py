# -*- coding: utf-8 -*-
import uuid
import unittest
import datetime
from time import sleep
from gevent.queue import Queue
from mock import patch, MagicMock
import requests_mock

from openprocurement.integrations.edr.databridge.edr_handler import EdrHandler
from openprocurement.integrations.edr.databridge.utils import Data
from openprocurement.integrations.edr.databridge.tests.utils import custom_sleep
from openprocurement.integrations.edr.client import ProxyClient




class TestEdrHandlerWorker(unittest.TestCase):

    def test_init(self):
        worker = EdrHandler.spawn(None, None, None, None)
        self.assertGreater(datetime.datetime.now().isoformat(),
                           worker.start_time.isoformat())

        self.assertEqual(worker.proxyClient, None)
        self.assertEqual(worker.edrpou_codes_queue, None)
        self.assertEqual(worker.edr_ids_queue, None)
        self.assertEqual(worker.upload_to_doc_service_queue, None)
        self.assertEqual(worker.delay, 15)
        self.assertEqual(worker.exit, False)

        worker.shutdown()
        self.assertEqual(worker.exit, True)
        del worker

    @requests_mock.Mocker()
    @patch('gevent.sleep')
    def test_proxy_client(self, mrequest, gevent_sleep):
        """ Test that proxy return json with id """
        gevent_sleep.side_effect = custom_sleep
        proxy_client = ProxyClient(host='127.0.0.1', port='80', token='')
        mrequest.get("{uri}".format(uri=proxy_client.verify_url),
                     [{'json': [{'id': '123'}], 'status_code': 200},
                      {'json': [{'id': '321'}], 'status_code': 200}])

        edrpou_codes_queue = Queue(10)
        edrpou_codes_queue.put(Data(uuid.uuid4().hex, 'award_id', '123', "awards", None, None))
        edrpou_codes_queue.put(Data(uuid.uuid4().hex, 'award_id', '135', "awards", None, None))

        worker = EdrHandler.spawn(proxy_client, edrpou_codes_queue, MagicMock(), MagicMock())

        sleep(10)

        worker.shutdown()
        self.assertEqual(edrpou_codes_queue.qsize(), 0, 'Queue must be empty')
        self.assertEqual(mrequest.call_count, 2)
        self.assertEqual(mrequest.request_history[0].url,
                         u'127.0.0.1:80/verify?code=123')
        self.assertEqual(mrequest.request_history[1].url,
                         u'127.0.0.1:80/verify?code=135')

    @requests_mock.Mocker()
    @patch('gevent.sleep')
    def test_proxy_client_401(self, mrequest, gevent_sleep):
        """ After 401 need restart worker """
        gevent_sleep.side_effect = custom_sleep
        proxy_client = ProxyClient(host='127.0.0.1', port='80', token='')
        mrequest.get("{uri}".format(uri=proxy_client.verify_url),
                     [{'text': '', 'status_code': 401},
                      {'json': [{'id': '321'}], 'status_code': 200},
                      {'json': [{'id': '333'}], 'status_code': 200}])

        edrpou_codes_queue = Queue(10)
        edrpou_codes_queue.put(Data(uuid.uuid4().hex, 'award_id', '123', "awards", None, None))
        edrpou_codes_queue.put(Data(uuid.uuid4().hex, 'award_id', '135', "awards", None, None))

        worker = EdrHandler.spawn(proxy_client, edrpou_codes_queue,
                                  MagicMock(), MagicMock())

        sleep(5)
        worker.shutdown()
        self.assertEqual(edrpou_codes_queue.qsize(), 0, 'Queue must be empty')
        self.assertEqual(mrequest.call_count, 3)  # Requests must call proxy three times
        self.assertEqual(mrequest.request_history[0].url,
                         u'127.0.0.1:80/verify?code=123')  # First return 401
        self.assertEqual(mrequest.request_history[1].url,
                         u'127.0.0.1:80/verify?code=123')  # From retry
        self.assertEqual(mrequest.request_history[2].url,
                         u'127.0.0.1:80/verify?code=135')  # Resume normal work


    @requests_mock.Mocker()
    @patch('gevent.sleep')
    def test_proxy_client_429(self, mrequest, gevent_sleep):
        gevent_sleep.side_effect = custom_sleep
        proxy_client = ProxyClient(host='127.0.0.1', port='80', token='')
        mrequest.get("{uri}".format(uri=proxy_client.verify_url),
                     [{'text': '', 'status_code': 429, 'headers': {'Retry-After': '10'}},
                      {'json': [{'id': '321'}], 'status_code': 200},
                      {'json': [{'id': '333'}], 'status_code': 200}])

        edrpou_codes_queue = Queue(10)
        edrpou_codes_queue.put(Data(uuid.uuid4().hex, 'award_id', '123', "awards", None, None))
        edrpou_codes_queue.put(Data(uuid.uuid4().hex, 'award_id', '135', "awards", None, None))

        worker = EdrHandler.spawn(proxy_client, edrpou_codes_queue, MagicMock(), MagicMock())

        sleep(5)
        worker.shutdown()
        self.assertEqual(edrpou_codes_queue.qsize(), 0, 'Queue must be empty')
        self.assertEqual(mrequest.call_count, 3)  # Requests must call proxy three times
        self.assertEqual(mrequest.request_history[0].url,
                         u'127.0.0.1:80/verify?code=123')  # First return 429
        self.assertEqual(mrequest.request_history[1].url,
                         u'127.0.0.1:80/verify?code=123')
        self.assertEqual(mrequest.request_history[2].url,
                         u'127.0.0.1:80/verify?code=135')

    @requests_mock.Mocker()
    @patch('gevent.sleep')
    def test_proxy_client_402(self, mrequest, gevent_sleep):
        gevent_sleep.side_effect = custom_sleep
        proxy_client = ProxyClient(host='127.0.0.1', port='80', token='')
        mrequest.get("{uri}".format(uri=proxy_client.verify_url),
                     [{'text': '', 'status_code': 402},  # pay for me
                      {'json': [{'id': '321'}], 'status_code': 200},
                      {'json': [{'id': '333'}], 'status_code': 200}])

        edrpou_codes_queue = Queue(10)
        edrpou_codes_queue.put(Data(uuid.uuid4().hex, 'award_id', '123', "awards", None, None))
        edrpou_codes_queue.put(
            Data(uuid.uuid4().hex, 'award_id', '135', "awards", None, None))

        worker = EdrHandler.spawn(proxy_client, edrpou_codes_queue,
                                  MagicMock(), MagicMock())

        sleep(5)
        worker.shutdown()
        self.assertEqual(edrpou_codes_queue.qsize(), 0, 'Queue must be empty')
        self.assertEqual(mrequest.call_count, 3)  # Requests must call proxy three times
        self.assertEqual(mrequest.request_history[0].url,
                         u'127.0.0.1:80/verify?code=123')  # First return 402
        self.assertEqual(mrequest.request_history[1].url,
                         u'127.0.0.1:80/verify?code=123')
        self.assertEqual(mrequest.request_history[2].url,
                         u'127.0.0.1:80/verify?code=135')
