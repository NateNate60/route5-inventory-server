import flask
import datetime
import json
import flask_jwt_extended
from passlib.hash import bcrypt
from database import get_db

login = flask.Blueprint('login', __name__)

@login.route("/v1/login", methods=["POST"])
def password_login () :

    data = flask.request.get_json()

    if "username" not in data or "password" not in data:
        return flask.Response('{"error": "Username or password not provided"}', status=400)
    
    username = data["username"]
    password = data["password"]
    stay_in = data["stay_in"] if "stay_in" in data else False

    record = get_db("route5")["users"].find_one({"username": username})
    if record is None:
        return flask.Response('{"error": "Username not found"}', status=401)
    if not bcrypt.verify(password, record["password_hash"]) :
        return flask.Response('{"error": "Password is incorrect"}', status=401)
    
    org = record["org"]
    
    access_token = flask_jwt_extended.create_access_token(identity=username, additional_claims={
        "org": org,
        "is_admin": "admin" in record["roles"]
    })
    refresh_token = flask_jwt_extended.create_refresh_token(identity=username, additional_claims={
        "org": org,
        "is_admin": "admin" in record["roles"]
    })
    response = flask.jsonify({
        "access_token": access_token,
        "refresh_token": refresh_token
    })
    return response


@login.route("/v1/login/tokens/access", methods=["GET"])
@flask_jwt_extended.jwt_required(refresh=True)
def get_access_token ():
    identity = flask_jwt_extended.get_jwt_identity()
    jwt = flask_jwt_extended.get_jwt()
    access_token = flask_jwt_extended.create_access_token(identity=identity, additional_claims={
        "org": jwt["org"],
        "is_admin": jwt["is_admin"],
        "username": identity,
    })
    return flask.jsonify(access_token=access_token)

@login.route("/v1/login/tokens/access/validity", methods=["GET"])
@flask_jwt_extended.jwt_required()
def check_access_token ():
    identity = flask_jwt_extended.get_jwt_identity()
    jwt = flask_jwt_extended.get_jwt()
    token = flask_jwt_extended.verify_jwt_in_request()
    return flask.jsonify(
        {
            "username": identity,
            "org": jwt["org"],
            "expiration": datetime.datetime.fromtimestamp(token[1]["exp"], tz=datetime.timezone.utc).isoformat() + "Z"
        }
    )