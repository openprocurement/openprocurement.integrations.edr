# -*- coding: utf-8 -*-

from pyramid.security import (
    ALL_PERMISSIONS,
    Allow,
    Deny,
    Everyone,
)


class Root(object):
    __name__ = None
    __parent__ = None
    __acl__ = [
        # (Allow, Everyone, ALL_PERMISSIONS),
        (Allow, Everyone, 'view_tender'),
        (Deny, 'broker05', 'create_bid'),
        (Deny, 'broker05', 'create_complaint'),
        (Deny, 'broker05', 'create_question'),
        (Deny, 'broker05', 'create_tender'),
        (Allow, 'g:brokers', 'verify'),
        (Allow, 'g:admins', ALL_PERMISSIONS),
    ]

    def __init__(self, request):
        self.request = request


def factory(request):
    root = Root(request)
    return root
