import flask
import datetime

import json
import tcgplayer
import config
from database import get_db
from flask_jwt_extended import jwt_required, get_jwt

saved_comps = flask.Blueprint('saved_comps', __name__)

def validate (data) -> flask.Response | None:
    green_cart = data.get("green_cart")
    orange_cart = data.get("orange_cart")
    money_given = data.get("money_given")
    money_received = data.get("money_received")
    credit_given = data.get("credit_given")
    credit_received = data.get("credit_received")
    payment_method_received = data.get("payment_method_received")
    payment_method_given = data.get("payment_method_given")

    if (type(green_cart) is not dict or type(orange_cart) is not dict
        or type(money_given) is not int or type(money_received) is not int
        or type(credit_given) is not int or type(credit_received) is not int
        or type(payment_method_given) is not str or type(payment_method_received) is not str):
        return flask.Response('{"error": "One or more fields is not the right type"}', status=400)
    if "products" not in green_cart:
        return flask.Response('{"error": "Green cart is missing products"}', status=400)
    for itemID in green_cart["products"]:
        if type(itemID) is not str:
            return flask.Response('{' + f'"error": "Item ID {itemID} is not valid"' + '}')
        productQuantity = green_cart["products"][itemID]
        product = productQuantity.get("product")
        if type(productQuantity.get("quantity")) is not int or type(productQuantity.get("cashRate")) is not float or type(productQuantity.get("creditRate")) is not float or type(product) is not dict:
            return flask.Response('{' + f'"error": "Item with ID {itemID} is malformed"' + '}')
    return None

@saved_comps.route("/v1/savedcomps", methods=["POST"])
@jwt_required()
def save_comp():
    claims = get_jwt()
    data = flask.request.get_json()

    validation = validate(data)
    if type(validation) is flask.Response:
        return validation
        
    database = get_db()
    cursor = database.cursor()

    cursor.execute("INSERT INTO Comps VALUES (NULL, %s, %s, NOW(), %s, NOW(), %s, %s)", (
        claims["org"],
        data.get("name"),
        claims["username"],
        claims["username"],
        json.dumps(data)
    ))
    database.commit()
    database.close()
    return {}

@saved_comps.route("/v1/savedcomps", methods=["GET"])
@jwt_required()
def get_comp():
    claims = get_jwt()
        
    database = get_db()
    cursor = database.cursor()

    cursor.execute("SELECT * FROM Comps WHERE org = %s", (
        claims["org"],
    ))
    r = cursor.fetchall()
    comps = []
    for comp in r:
        data = json.loads(comp[7])
        comps.append({
            "id": comp[0],
            "name": comp[2],
            "green_cart": data["green_cart"],
            "orange_cart": data["orange_cart"],
            "credit_received": data["credit_received"],
            "credit_given": data["credit_given"],
            "money_received": data["money_received"],
            "money_given": data["money_given"],
            "payment_method_received": data["payment_method_received"],
            "payment_method_given": data["payment_method_given"],
            "created_date": comp[3].timestamp(),
            "created_by": comp[4],
            "modified_date": comp[5].timestamp(),
            "modified_by": comp[6],
            
        })
    database.commit()
    database.close()
    return comps

@saved_comps.route("/v1/savedcomps", methods=["DELETE"])
@jwt_required()
def delete_comp():
    claims = get_jwt()

    id = flask.request.args.get("id")

    if id is None:
        return flask.Response('{"error": "ID not provided"}', status=400)

    database = get_db()
    cursor = database.cursor()

    cursor.execute("DELETE FROM Comps WHERE org = %s AND id = %s", (
        claims["org"],
        id
    ))
    rowcount = cursor.rowcount
    database.commit()
    database.close()
    if rowcount == 0:
        return flask.Response('{"error": "Could not find saved comp with that ID"}', status=404)
    else:
        return flask.Response(status=200)