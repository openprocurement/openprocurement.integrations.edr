# -*- coding: utf-8 -*-
from gevent import monkey
from gevent.queue import Queue
from retrying import retry
monkey.patch_all()

try:
    import urllib3.contrib.pyopenssl
    urllib3.contrib.pyopenssl.inject_into_urllib3()
except ImportError:
    pass

import logging.config
import gevent
from datetime import datetime
from gevent import Greenlet, spawn

from openprocurement.integrations.edr.databridge.journal_msg_ids import (
    DATABRIDGE_GET_TENDER_FROM_QUEUE, DATABRIDGE_START_EDR_HANDLER,
    DATABRIDGE_UNAUTHORIZED_EDR, DATABRIDGE_SUCCESS_CREATE_FILE,
    DATABRIDGE_EMPTY_RESPONSE
)
from openprocurement.integrations.edr.databridge.utils import (
    Data, journal_context, validate_param, RetryException
)

logger = logging.getLogger(__name__)


class EdrHandler(Greenlet):
    """ Edr API Data Bridge """
    error_details = {'error': 'Couldn\'t find this code in EDR.'}
    identification_scheme = u"UA-EDR"
    activityKind_scheme = u'КВЕД'

    def __init__(self, proxyClient, edrpou_codes_queue, edr_ids_queue, upload_to_doc_service_queue, delay=15):
        super(EdrHandler, self).__init__()
        self.exit = False
        self.start_time = datetime.now()

        # init clients
        self.proxyClient = proxyClient

        # init queues for workers
        self.edrpou_codes_queue = edrpou_codes_queue
        self.edr_ids_queue = edr_ids_queue
        self.upload_to_doc_service_queue = upload_to_doc_service_queue

        # retry queues for workers
        self.retry_edrpou_codes_queue = Queue(maxsize=500)
        self.retry_edr_ids_queue = Queue(maxsize=500)

        # blockers
        self.until_too_many_requests_event = gevent.event.Event()

        self.until_too_many_requests_event.set()

        self.delay = delay

    def prepare_data(self, data):
        additional_activity_kinds = []
        primary_activity_kind = {}
        for activity_kind in data.get('activity_kinds', []):
            if activity_kind.get('is_primary'):
                primary_activity_kind = {'id': activity_kind.get('code'),
                                         'scheme': self.activityKind_scheme,
                                         'description': activity_kind.get('name')}
            else:
                additional_activity_kinds.append({'id': activity_kind.get('code'),
                                                  'scheme': self.activityKind_scheme,
                                                  'description': activity_kind.get('name')})
        return {'name': data.get('names').get('short') if data.get('names') else None,
                'identification': {'scheme': self.identification_scheme,
                                   'id': data.get('code'),
                                   'legalName': data.get('names').get('display') if data.get('names') else None},
                'founders': data.get('founders'),
                'management': data.get('management'),
                'activityKind': primary_activity_kind or None,
                'additionalActivityKinds': additional_activity_kinds or None,
                'address': {'streetAddress': data.get('address').get('address') if data.get('address') else None,
                            'postalCode': data.get('address').get('zip') if data.get('address') else None,
                            'countryName': data.get('address').get('country') if data.get('address') else None}}

    def get_edr_id(self):
        """Get data from edrpou_codes_queue; make request to EDR Api, passing EDRPOU (IPN, passport); Received ids is
        put into Data.edr_ids variable; Data variable placed to edr_ids_queue."""
        while True:
            tender_data = self.edrpou_codes_queue.get()
            logger.info('Get tender {} from edrpou_codes_queue'.format(tender_data.tender_id),
                        extra=journal_context({"MESSAGE_ID": DATABRIDGE_GET_TENDER_FROM_QUEUE},
                                              params={"TENDER_ID": tender_data.tender_id}))
            gevent.wait([self.until_too_many_requests_event])
            response = self.proxyClient.verify(validate_param(tender_data.code), tender_data.code)
            if response.status_code == 403 and response.json().get('errors')[0].get('description') == [{"message": "EDRPOU not found"}]:
                logger.info('Empty response for tender {}.'.format(tender_data.tender_id),
                            extra=journal_context({"MESSAGE_ID": DATABRIDGE_EMPTY_RESPONSE},
                                                  params={"TENDER_ID": tender_data.tender_id}))
                data = Data(tender_data.tender_id, tender_data.item_id, tender_data.code,
                            tender_data.item_name, response.json(), self.error_details)
                self.upload_to_doc_service_queue.put(data)  # Given EDRPOU code not found, file with error put into upload_to_doc_service_queue
                continue
            if response.status_code == 200:
                # Create new Data object. Write to Data.code list of edr ids from EDR.
                # List because EDR can return 0, 1 or 2 values to our reques
                data = Data(tender_data.tender_id, tender_data.item_id, tender_data.code,
                            tender_data.item_name, [edr_ids['id'] for edr_ids in response.json()], None)
                self.edr_ids_queue.put(data)
                logger.info('Put tender {} {} {} to edr_ids_queue.'.format(tender_data.tender_id,
                                                                           tender_data.item_name,
                                                                           tender_data.item_id))
            else:
                self.retry_edrpou_codes_queue.put(tender_data)  # Put tender to retry
                self.handle_status_response(response, tender_data.tender_id)
                logger.info('Put tender {} with {} id {} to retry_edrpou_codes_queue'.format(
                    tender_data.tender_id, tender_data.item_name, tender_data.item_id),
                    extra=journal_context(params={"TENDER_ID": tender_data.tender_id}))
            gevent.sleep(0)

    def retry_get_edr_id(self):
        """Get data from retry_edrpou_codes_queue; Put data into edr_ids_queue if request is successful, otherwise put
        data back to retry_edrpou_codes_queue."""
        tender_data = self.retry_edrpou_codes_queue.get()
        logger.info('Get tender {} from retry_edrpou_codes_queue'.format(tender_data.tender_id),
                    extra=journal_context({"MESSAGE_ID": DATABRIDGE_GET_TENDER_FROM_QUEUE},
                                          params={"TENDER_ID": tender_data.tender_id}))
        gevent.wait([self.until_too_many_requests_event])
        try:
            response = self.get_edr_id_request(validate_param(tender_data.code), tender_data.code)
        except RetryException as re:
            logger.info("RetryException error message {}".format(re.args[0]))
            self.handle_status_response(re.args[1], tender_data.tender_id)
            self.retry_edrpou_codes_queue.put(tender_data)
            logger.info('Put tender {} with {} id {} to retry_edrpou_codes_queue'.format(
                tender_data.tender_id, tender_data.item_name, tender_data.item_id),
                extra=journal_context(params={"TENDER_ID": tender_data.tender_id}))
            gevent.sleep(0)
        except Exception:
            self.retry_edrpou_codes_queue.put(tender_data)
            logger.info('Put tender {} with {} id {} to retry_edrpou_codes_queue'.format(
                tender_data.tender_id, tender_data.item_name, tender_data.item_id),
                extra=journal_context(params={"TENDER_ID": tender_data.tender_id}))
            gevent.sleep(0)
        else:
            if not response.json():
                logger.info('Empty response for tender {}.'.format(tender_data.tender_id),
                            extra=journal_context({"MESSAGE_ID": DATABRIDGE_EMPTY_RESPONSE},
                                                  params={"TENDER_ID": tender_data.tender_id}))
                data = Data(tender_data.tender_id, tender_data.item_id, tender_data.code,
                            tender_data.item_name, response.json(), self.error_details)
                self.upload_to_doc_service_queue.put(data)
            # Create new Data object. Write to Data.code list of edr ids from EDR.
            # List because EDR can return 0, 1 or 2 values to our request
            data = Data(tender_data.tender_id, tender_data.item_id, tender_data.code,
                        tender_data.item_name, [obj['id'] for obj in response.json()], None)
            self.edr_ids_queue.put(data)
            logger.info('Put tender {} {} {} to edr_ids_queue.'.format(tender_data.tender_id,
                                                                       tender_data.item_name,
                                                                       tender_data.item_id))

    @retry(stop_max_attempt_number=5, wait_exponential_multiplier=1000)
    def get_edr_id_request(self, param, code):
        """Execute request to EDR Api for retry queue objects."""
        response = self.proxyClient.verify(param, code)
        if response.status_code != 200:
            raise RetryException('Unsuccessful retry request to EDR.', response)
        return response

    def get_edr_details(self):
        """Get data from edr_ids_queue; make request to EDR Api for detailed info; Required fields is put to
        Data.file_content variable, Data object is put to upload_to_doc_service_queue."""
        while True:
            tender_data = self.edr_ids_queue.get()
            logger.info('Get edr ids {}  tender {} from edr_ids_queue'.format(tender_data.edr_ids, tender_data.tender_id),
                        extra=journal_context({"MESSAGE_ID": DATABRIDGE_GET_TENDER_FROM_QUEUE},
                                              params={"TENDER_ID": tender_data.tender_id}))
            gevent.wait([self.until_too_many_requests_event])
            for edr_id in tender_data.edr_ids:
                response = self.proxyClient.details(edr_id)
                if response.status_code == 200:
                    data = Data(tender_data.tender_id, tender_data.item_id, tender_data.code,
                                tender_data.item_name, tender_data.edr_ids,
                                self.prepare_data(response.json()))
                    self.upload_to_doc_service_queue.put(data)
                    logger.info('Successfully created file for tender {} {} {}'.format(
                        tender_data.tender_id, tender_data.item_name, tender_data.item_id),
                        extra=journal_context({"MESSAGE_ID": DATABRIDGE_SUCCESS_CREATE_FILE},
                                              params={"TENDER_ID": tender_data.tender_id}))
                    tender_data.edr_ids.remove(edr_id)  # remove from list edr_id that have successful response
                else:
                    self.retry_edr_ids_queue.put(tender_data)
                    logger.info('Put tender {} with {} id {} to retry_edr_ids_queue'.format(
                                tender_data.tender_id, tender_data.item_name, tender_data.item_id),
                            extra=journal_context(params={"TENDER_ID": tender_data.tender_id}))
                    gevent.sleep(0)

    def retry_get_edr_details(self):
        """Get data from retry_edr_ids_queue; Put data into upload_to_doc_service_queue if request is successful, otherwise put
        data back to retry_edr_ids_queue."""
        while True:
            tender_data = self.retry_edr_ids_queue.get()
            logger.info('Get edr ids {}  tender {} from retry_edr_ids_queue'.format(tender_data.edr_ids,
                                                                                    tender_data.tender_id),
                        extra=journal_context({"MESSAGE_ID": DATABRIDGE_GET_TENDER_FROM_QUEUE},
                                              params={"TENDER_ID": tender_data.tender_id}))
            gevent.wait([self.until_too_many_requests_event])
            for edr_id in tender_data.edr_ids:
                try:
                    response = self.get_edr_details_request(edr_id)
                except Exception:
                    self.retry_edr_ids_queue.put(tender_data)
                    logger.info('Put tender {} with {} id {} to retry_edr_ids_queue'.format(
                        tender_data.tender_id, tender_data.item_name, tender_data.item_id),
                        extra=journal_context(params={"TENDER_ID": tender_data.tender_id}))
                    gevent.sleep(0)
                else:
                    data = Data(tender_data.tender_id, tender_data.item_id, tender_data.code,
                                tender_data.item_name, tender_data.edr_ids,
                                {key: value for key, value in response.json().items() if key in self.required_fields})
                    self.upload_to_doc_service_queue.put(data)
                    logger.info('Successfully created file for tender {} {} {}'.format(
                        tender_data.tender_id, tender_data.item_name, tender_data.item_id),
                        extra=journal_context({"MESSAGE_ID": DATABRIDGE_SUCCESS_CREATE_FILE},
                                              params={"TENDER_ID": tender_data.tender_id}))
                    tender_data.edr_ids.remove(edr_id)  # remove from list edr_id that have successful response

    @retry(stop_max_attempt_number=5, wait_exponential_multiplier=1000)
    def get_edr_details_request(self, edr_id):
        """Execute request to EDR Api to get detailed info for retry queue objects."""
        response = self.proxyClient.details(edr_id)
        if response.status_code != 200:
            raise RetryException('Unsuccessful retry request to EDR.', response)
        return response

    def handle_status_response(self, response, tender_id):
        """Process unsuccessful request"""
        if response.status_code == 401:
            logger.info('Not Authorized (invalid token) for tender {}'.format(tender_id),
                        extra=journal_context({"MESSAGE_ID": DATABRIDGE_UNAUTHORIZED_EDR}, {"TENDER_ID": tender_id}))
            raise Exception('Invalid EDR API token')
        elif response.status_code == 429:
            self.until_too_many_requests_event.clear()
            gevent.sleep(response.headers.get('Retry-After', self.delay))
            self.until_too_many_requests_event.set()
        elif response.status_code == 402:
            logger.info('Payment required for requesting info to EDR. '
                        'Error description: {err}'.format(err=response.text),
                        extra=journal_context(params={"TENDER_ID": tender_id}))
            raise Exception('Payment required for requesting info to EDR.')
        else:
            logger.info('Error appeared while requesting to EDR. '
                        'Description: {err}'.format(err=response.text),
                        extra=journal_context(params={"TENDER_ID": tender_id}))

    def _run(self):
        logger.info('Start EDR Handler', extra=journal_context({"MESSAGE_ID": DATABRIDGE_START_EDR_HANDLER}, {}))
        self.immortal_jobs = {'get_edr_id': spawn(self.get_edr_id),
                              'get_edr_details': spawn(self.get_edr_details),
                              'retry_get_edr_id': spawn(self.retry_get_edr_id),
                              'retry_get_edr_details': spawn(self.retry_get_edr_details)}

        try:
            while not self.exit:
                gevent.sleep(self.delay)
                for name, job in self.immortal_jobs.items():
                    if job.dead:
                        logger.warning("EDR handler worker {} dead try restart".format(name),
                                       extra=journal_context({"MESSAGE_ID": "DATABRIDGE_RESTART_{}".format(name.lower())}, {}))
                        self.immortal_jobs[name] = gevent.spawn(getattr(self, name))
                        logger.info("EDR handler worker {} is up".format(name))
        except Exception as e:
            logger.error(e)
            gevent.killall(self.immortal_jobs.values(), timeout=5)

    def shutdown(self):
        self.exit = True
        logger.info('Worker EDR Handler complete his job.')
