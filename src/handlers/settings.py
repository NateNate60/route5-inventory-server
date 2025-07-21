import flask
from flask_jwt_extended import jwt_required

from database import DATABASE

settings = flask.Blueprint('settings', __name__)

@settings.route("/v1/settings/rates", methods=["GET", "PATCH"])
@jwt_required()
def buyrates () :
    if flask.request.method == "PATCH":
        data = flask.request.json

        # validation
        MALFORMED_DATA = flask.Response('{"error": "Missing one or more required fiels"}', status=422)
        if "cutoffs" not in data or "cash_rates" not in data or "credit_rates" not in data:
            return MALFORMED_DATA
        for i in ("card", "slab", "sealed"):
            if i not in data["cutoffs"] or i not in data["cash_rates"] or i not in data["credit_rates"]:
                return MALFORMED_DATA
            if type(data["cutoffs"][i]) != list or type(data["cash_rates"][i]) != list or type(data["credit_rates"][i]) != list:
                return MALFORMED_DATA
            
            cutoffs_length = len(data["cutoffs"][i])

            if len(data["cash_rates"][i]) != cutoffs_length + 1 or len(data["cash_rates"][i]) != cutoffs_length + 1:
                return MALFORMED_DATA
        
        data["id"] = "rates"

        DATABASE["settings"].replace_one({"id": "rates"}, data)

        return flask.Response(status=204)

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