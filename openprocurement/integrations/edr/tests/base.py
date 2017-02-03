from openprocurement.api.tests.base import BaseWebTest as _BaseWebTest
import os


class BaseWebTest(_BaseWebTest):

    """Base Web Test to test openprocurement.api.

    It setups the database before each test and delete it after.
    """

    relative_to = os.path.dirname(__file__)  # crafty line
