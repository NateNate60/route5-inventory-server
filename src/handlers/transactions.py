import flask
from flask_jwt_extended import jwt_required

from database import DATABASE
from datetime import datetime

transactions = flask.Blueprint('transactions', __name__)

@transactions.route("/v1/transaction")
@jwt_required()
def get_transaction ():
    id = flask.request.args.get("id")
    if id == None:
        return flask.Response({"error": "No item ID provided"}, status=400)
    
    if id[:3] == "TXB":
        item = DATABASE["buys"].find_one({"txid": id})
    elif id[:3] == "TXS":
        item = DATABASE["sales"].find_one({"txid": id})
    elif id[:3] == "TXC":
        item = DATABASE["consignments"].find_one({"txid": id})
    else:
        return flask.Response({"error": "Malformed txid"}, status=400)
    if item is None:
        return flask.Response({"error": "txid not found"}, status=404)
    
    item.pop("_id")

    return item

@transactions.route("/v1/transaction/buys")
def get_buy_transactions ():

    
    start_date = flask.request.args.get("start_date")
    end_date = flask.request.args.get("end_date")

    cursor = DATABASE["buys"].find({"$and": [
        {
            "acquired_date": {"$gte": datetime(1980, 1, 1, 0, 0, 0) if start_date is None else datetime.fromisoformat(start_date.replace('Z', '+00:00'))}
        },
        {
            "acquired_date": {"$lte": datetime(9999, 1, 1, 0, 0, 0) if end_date is None else datetime.fromisoformat(end_date.replace('Z', '+00:00'))}
        }
    ]})
    data = []
    for thing in cursor:
        thing.pop("_id")
        if "credit_given" not in thing:
            thing["credit_given"] = 0
        if "payment_method" not in thing:
            thing["payment_method"] = "Unknown"
        thing["acquired_date"] = datetime.isoformat(thing["acquired_date"]) + 'Z'
        data.append(thing)
    return data

@transactions.route("/v1/transaction/sales")
def get_sale_transactions ():
    start_date = flask.request.args.get("start_date")
    end_date = flask.request.args.get("end_date")

    cursor = DATABASE["sales"].find({"$and": [
        {
            "sale_date": {"$gte": datetime(1980, 1, 1, 0, 0, 0) if start_date is None else datetime.fromisoformat(start_date.replace('Z', '+00:00'))}
        },
        {
            "sale_date": {"$lte": datetime(9999, 1, 1, 0, 0, 0) if end_date is None else datetime.fromisoformat(end_date.replace('Z', '+00:00'))}
        }
    ]})
    data = []
    for thing in cursor:
        thing.pop("_id")
        if "credit_applied" not in thing:
            thing["credit_applied"] = 0
        if "payment_method" not in thing:
            thing["payment_method"] = "Unknown"
        thing["sale_date"] = datetime.isoformat(thing["sale_date"]) + 'Z'
        data.append(thing)
    return data