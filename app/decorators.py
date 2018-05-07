from functools import wraps

from flask import abort, redirect, url_for
from flask_login import current_user


def permission_required(permission):
    """
    This decorator has been designed to restrict user permission

    :param permission:
    :return:
    """
    def permission_decorator(func):
        @wraps(func)
        def func_wrapper(*args, **kwargs):
            if current_user.is_authenticated:
                if current_user.role.name.lower() != permission.lower():
                    abort(403)
            return func(*args, **kwargs)
        return func_wrapper
    return permission_decorator


def check_user_confirmed(func):
    """
    This function has been designed to check if the user has been confirmed, otherwise redirect to the unconfirmed page
    :param func:
    :return:
    """
    @wraps(func)
    def func_wrapper(*args, **kwargs):
        if current_user.is_authenticated and not current_user.confirmed:
                return redirect(url_for('auth.unconfirmed'))
        return func(*args, **kwargs)
    return func_wrapper
