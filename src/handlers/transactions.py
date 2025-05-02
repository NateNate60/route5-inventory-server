import flask

from authentication import authenticate
from database import DATABASE

transactions = flask.Blueprint('transactions', __name__)

@transactions.route("/v1/transactions")
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