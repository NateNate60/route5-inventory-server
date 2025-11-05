import flask
from datetime import datetime, timezone
from passlib.hash import bcrypt
from flask_jwt_extended import get_jwt, jwt_required
from authentication import admin_required
from database import get_db

users = flask.Blueprint('users', __name__)

@users.route("/v1/users", methods=["GET"])
@jwt_required()
def get_users ():
    claims = get_jwt()
    DATABASE = get_db("route5")
    cursor = DATABASE["users"].find({"org": claims["org"]})
    list = []
    for user in cursor:
        created = user["created"].isoformat() 
        last_login =  user["last_logged_in"].isoformat()
        list.append({
            "username": user["username"],
            "roles": user["roles"],
            "created": created + "Z",
            "last_logged_in": last_login + "Z"
        })
    return flask.jsonify(list)

@users.route("/v1/users/add", methods=["POST"])
@jwt_required()
@admin_required()
def add_user ():
    claims = get_jwt()
    DATABASE = get_db("route5")

    data = flask.request.get_json()

    if "username" not in data or "password" not in data or "roles" not in data:
        return flask.Response('{"error": "Username or password or roles not provided"}', status=400)
    username = data['username']
    password = data['password']

    roles = data['roles']

    if DATABASE["users"].find_one({"username": username}) != None:
        return flask.Response('{"error": "That username is taken"}', status=409)
    DATABASE['users'].insert_one({
        "username": username,
        "password_hash": bcrypt.hash(password),
        "roles": roles,
        "org": claims["org"],
        "created": datetime.now(tz=timezone.utc),
        "last_logged_in": datetime.now(tz=timezone.utc)
    })

    return flask.Response("{}", status=201)

@users.route("/v1/users/rm", methods=["DELETE"])
@jwt_required()
@admin_required()
def rm_user ():
    claims = get_jwt()
    DATABASE = get_db("route5")

    username = flask.request.args.get("username")

    if username is None:
        return flask.Response('{"error": "Username not provided"}', status=400)
    DATABASE['users'].delete_one({"username": username, "org": claims["org"]})

    return flask.Response("{}", status=200)