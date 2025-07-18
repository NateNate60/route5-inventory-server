import flask
from flask_jwt_extended import jwt_required

from database import DATABASE

settings = flask.Blueprint('settings', __name__)

@settings.route("/v1/settings/rates", methods=["GET", "PATCH"])
@jwt_required()
def buyrates () :
    if flask.request.method == "PATCH":
        return flask.Response('{"error": "unimplemented"}', status=501)
    else:
        db_value = DATABASE["settings"].find_one({"id": "rates"})
        del db_value["_id"]
        return db_value

@settings.route("/v1/settings/threshhold", methods=["GET", "PATCH"])
@jwt_required()
def threshhold () :
    if flask.request.method == "PATCH":
        return flask.Response('{"error": "unimplemented"}', status=501)
    else:
        db_value = DATABASE["settings"].find_one({"id": "threshhold"})
        del db_value["_id"]
        return db_value