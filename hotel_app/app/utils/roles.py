from __future__ import annotations

from functools import wraps
from typing import Callable

from flask import abort
from flask_login import current_user

from ..models import UserRole


def role_required(*roles: UserRole) -> Callable:
    """Decorator restricting access to users with given roles."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role not in roles:
                return abort(403)
            return func(*args, **kwargs)

        return wrapper

    return decorator
