# -*- coding: utf-8 -*-


def authenticated_role(request):
    principals = request.effective_principals
    groups = [g for g in reversed(principals) if g.startswith('g:')]
    return groups[0][2:] if groups else 'anonymous'
