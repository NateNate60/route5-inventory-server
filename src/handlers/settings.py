import flask
import json
from flask_jwt_extended import get_jwt, jwt_required

from database import get_db

settings = flask.Blueprint('settings', __name__)

@settings.route("/v1/settings/rates", methods=["GET", "PATCH"])
@jwt_required()
def buyrates () :
    claims = get_jwt()

    if flask.request.method == "PATCH":
        data = flask.request.json

        if not claims.get("is_admin"):
            return flask.Response({"error": "Only admins can do this"}, status=403)

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
        MYSQL = get_db()
        cursor = MYSQL.cursor()
        cursor.execute('UPDATE Settings SET rates = %s WHERE org = %s', (json.dumps(data), claims["org"]))
        MYSQL.commit()
        cursor.close()
        MYSQL.close()
        return flask.Response('{}',status=200)
    else:
        MYSQL = get_db()
        cursor = MYSQL.cursor()
        cursor.execute("SELECT rates FROM Settings WHERE org = %s", (claims["org"],))
        rates = cursor.fetchone()
        cursor.close()
        MYSQL.close()
        return rates[0]

@settings.route("/v1/settings/threshold", methods=["GET", "PATCH"])
@jwt_required()
def threshhold () :
    claims = get_jwt()

    if flask.request.method == "PATCH":
        # validation
        if not claims.get("is_admin"):
            return flask.Response({"error": "Only admins can do this"}, status=403)
        if not flask.request.args.get("threshold"):
            return flask.Response({"error": "Threshold not provided"}, status=400)
        try:
            t = int(flask.request.args.get("threshold"))
        except ValueError:
            return flask.Response({"error": "Threshold must be int"}, status=400)
        
        MYSQL = get_db()
        cursor = MYSQL.cursor()
        cursor.execute("UPDATE Settings SET threshold = %s WHERE org = %s", (
            t,
            claims["org"]
        ))
        MYSQL.commit()
        cursor.close()
        MYSQL.close()
        return flask.Response({}, status=200)
    else:
        MYSQL = get_db()
        cursor = MYSQL.cursor()
        cursor.execute("SELECT threshold FROM Settings WHERE org = %s", (claims["org"],))
        value = cursor.fetchone()
        cursor.close()
        MYSQL.close()
        return {"value": value[0]}