from functools import wraps
from flask import abort
from flask_login import current_user
from app.models.usuario import RolEnum


def roles_required(*roles):
    """Restringe una vista a ciertos roles."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            if current_user.rol not in roles:
                abort(403)
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def admin_rrhh_required(fn):
    return roles_required(RolEnum.ADMIN_RRHH)(fn)


def jefe_o_admin_required(fn):
    return roles_required(RolEnum.ADMIN_RRHH, RolEnum.JEFE_AREA)(fn)
