# -*- coding: utf-8 -*-
import requests

from openprocurement.integrations.edr.timeout_handler import TimeoutHandler

from logging import getLogger
logger = getLogger(__name__)


class EdrClient(object):
    """Base class for making requests to EDR"""

    def __init__(self, host, yaml_keys, port=443, timeout_min=1, timeout_max=300, timeout_step=2, timeout_mode='mult'):
        self.session = requests.Session()
        self.url = '{host}:{port}/1.0/subjects'.format(host=host, port=port)
        self.yaml_keys = yaml_keys
        self.timeout_verify = TimeoutHandler(timeout_min, timeout_max, timeout_step, timeout_mode)
        self.timeout_details = TimeoutHandler(timeout_min, timeout_max, timeout_step, timeout_mode)

    def cycle_keys(self, url, timeout, role):
        keys = self.yaml_keys[role]
        for key in keys:
            response = self._do_request(url, timeout, key)
            if response.status_code == 200:
                return response
        return response

    def _do_request(self, url, timeout, key):
        headers = {"Accept": "application/json",
                   "Authorization": "Token {token}".format(token=key)}
        try:
            response = self.session.get(url=url, headers=headers, timeout=timeout.value)
            timeout.update(True)
            return response
        except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectTimeout):
            if not timeout.update(False):
                logger.fatal('Timeout maxed out! Value: {0}'.format(timeout.value))
            raise

    def get_subject(self, role, param, code):
        """
        Send request to EDR using EDRPOU (physical entity-entrepreneur) code or passport.
        In response we except list of subjects with unique id in each subject.
        List mostly contains 1 subject, but occasionally includes 2 or none.
        """
        return self.cycle_keys('{url}?{param}={code}'.format(url=self.url, param=param, code=code),
                               self.timeout_verify, role)

    def get_subject_details(self, role, edr_unique_id):
        """
        Send request to EDR using unique identifier to get subject's details.
        """
        return self.cycle_keys('{url}/{id}'.format(url=self.url, id=edr_unique_id),
                               self.timeout_details, role)
