import flask
from passlib.hash import bcrypt
from flask_jwt_extended import jwt_required

from database import DATABASE

users = flask.Blueprint('users', __name__)

@users.route("/v1/users/add", methods=["POST"])
@jwt_required()
def add_user ():
    data = flask.request.get_json()

    if "username" not in data or "password" not in data or "roles" not in data:
        return flask.Response('{"error": "Username or password or roles not provided"}', status=400)
    username = data['username']
    password = data['password']
    roles = data['roles']

    DATABASE['users'].insert_one({
        "username": username,
        "password_hash": bcrypt.hash(password),
        "roles": roles
    })

    return flask.Response("{}", status=201)