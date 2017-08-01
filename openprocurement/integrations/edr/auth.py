# -*- coding: utf-8 -*-


def authenticated_role(request):
    principals = request.effective_principals
    groups = [g for g in reversed(principals) if g.startswith('g:')]
    return groups[0][2:] if groups else 'anonymous'


def user(request):
    principals = request.effective_principals
    user_id = [u for u in principals if not u.lower().startswith("system") and not u.lower().startswith("g:")][0]
    return user_id if user_id else 'anonymous'
