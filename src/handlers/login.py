import flask
import datetime
import json
import flask_jwt_extended
from passlib.hash import bcrypt
from database import DATABASE

login = flask.Blueprint('login', __name__)

@login.route("/v1/login", methods=["POST"])
def password_login () :
    data = flask.request.get_json()

    if "username" not in data or "password" not in data:
        return flask.Response('{"error": "Username or password not provided"}', status=400)
    
    username = data["username"]
    password = data["password"]
    stay_in = data["stay_in"] if "stay_in" in data else False

    record = DATABASE["users"].find_one({"username": username})
    if record is None:
        return flask.Response('{"error": "Username not found"}', status=401)
    if not bcrypt.verify(password, record["password_hash"]) :
        return flask.Response('{"error": "Password is incorrect"}', status=401)
    
    access_token = flask_jwt_extended.create_access_token(identity=username)
    refresh_token = flask_jwt_extended.create_refresh_token(identity=username)
    response = flask.jsonify({
        "access_token": access_token,
        "refresh_token": refresh_token
    })
    return response


@login.route("/v1/login/tokens/access", methods=["GET"])
@flask_jwt_extended.jwt_required(refresh=True)
def get_access_token ():
    identity = flask_jwt_extended.get_jwt_identity()
    access_token = flask_jwt_extended.create_access_token(identity=identity)
    return flask.jsonify(access_token=access_token)

@login.route("/v1/login/tokens/access/validity", methods=["GET"])
@flask_jwt_extended.jwt_required()
def check_access_token ():
    identity = flask_jwt_extended.get_jwt_identity()
    token = flask_jwt_extended.verify_jwt_in_request()
    return flask.jsonify(
        {
            "username": identity,
            "expiration": token[1]["exp"]
        }
    )