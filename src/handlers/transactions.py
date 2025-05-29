import flask

from authentication import authenticate
from database import DATABASE
from datetime import datetime

transactions = flask.Blueprint('transactions', __name__)

@transactions.route("/v1/transaction")
def get_transaction ():
    user = authenticate(flask.request.headers.get("Authorization"))
    if user == "":
        return flask.Response({}, status=401)
    
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
    user = authenticate(flask.request.headers.get("Authorization"))
    if user == "":
        return flask.Response({}, status=401)
    
    start_date = flask.request.args.get("start_date")
    end_date = flask.request.args.get("end_date")

    cursor = DATABASE["buys"].find({"$and": [
        {
            "acquired_date": {"$gte": datetime(1980, 1, 1, 0, 0, 0) if start_date is None else datetime.fromisocalendar(start_date)}
        },
        {
            "acquired_date": {"$lte": datetime(9999, 1, 1, 0, 0, 0) if end_date is None else datetime.fromisocalendar(end_date)}
        }
    ]})
    data = []
    for thing in cursor:
        thing.pop("_id")
        data.append(thing)
    return data

@transactions.route("/v1/transaction/sales")
def get_buy_transactions ():
    user = authenticate(flask.request.headers.get("Authorization"))
    if user == "":
        return flask.Response({}, status=401)
    
    start_date = flask.request.args.get("start_date")
    end_date = flask.request.args.get("end_date")

    cursor = DATABASE["sales"].find({"$and": [
        {
            "acquired_date": {"$gte": datetime(1980, 1, 1, 0, 0, 0) if start_date is None else datetime.fromisocalendar(start_date)}
        },
        {
            "acquired_date": {"$lte": datetime(9999, 1, 1, 0, 0, 0) if end_date is None else datetime.fromisocalendar(end_date)}
        }
    ]})
    data = []
    for thing in cursor:
        thing.pop("_id")
        data.append(thing)
    return data