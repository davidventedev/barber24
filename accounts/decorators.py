from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect


def role_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped(request, *args, **kwargs):
            user = request.user
            if user.is_superadmin_role:
                return view_func(request, *args, **kwargs)
            if user.role not in roles:
                raise PermissionDenied
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator


def shop_required(view_func):
    @wraps(view_func)
    @login_required
    def _wrapped(request, *args, **kwargs):
        if request.user.is_superadmin_role:
            return view_func(request, *args, **kwargs)
        if not request.user.shop_id:
            return redirect('dashboard:home')
        return view_func(request, *args, **kwargs)
    return _wrapped
