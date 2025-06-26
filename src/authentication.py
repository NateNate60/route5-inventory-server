import flask
from flask_jwt_extended import get_jwt
from flask_jwt_extended import verify_jwt_in_request
from functools import wraps

def admin_required():
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            if "is_admin" in claims and claims["is_admin"]:
                return fn(*args, **kwargs)
            else:
                return flask.Response('{"error": "Only admins are allowed to do that"}', status=403)

        return decorator

    return wrapper