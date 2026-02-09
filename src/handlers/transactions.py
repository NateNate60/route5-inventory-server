import flask
from flask_jwt_extended import get_jwt, jwt_required

from datetime import datetime
from mysql import connector

import config
from database import get_db

transactions = flask.Blueprint('transactions', __name__)

@transactions.route("/v1/transaction")
@jwt_required()
def get_transaction ():
    claims = get_jwt()
    DATABASE = get_db(claims["org"])
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
@jwt_required()
def get_buy_transactions ():
    claims = get_jwt()
    DATABASE = get_db(claims["org"])
    
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
@jwt_required()
def get_sale_transactions ():
    claims = get_jwt()
    DATABASE = get_db(claims["org"])
    
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

@transactions.route("/v1/transaction/tcgplayer")
@jwt_required()
def export_tcg_csv ():
    claims = get_jwt()
    DATABASE = get_db(claims["org"])

    txid = flask.request.args.get("txid")

    if not txid:
        return flask.Response({"error": "No TXID provided"}, status=400)

    tx = DATABASE["buys"].find_one({"txid": txid})
    if tx is None:
        return flask.Response({"error": "TXID not found"}, status=404)
    
    MYSQL = connector.connect(host="localhost", user=config.MYSQL_USER, password=config.MYSQL_PASSWORD, database="route5prices", connection_timeout=3600)
    cursor = MYSQL.cursor()

    items = []
    for item in tx["items"]:
        if item["id"][0] != "B":
            # Skip if it is not bulk
            continue
        CONDITION_MATRIX = {
            "NM": "nm_market_price",
            "LP": "lp_market_price",
            "MP": "mp_market_price",
            "HP": "hp_market_price",
            "DM": "dm_market_price"
        }
        condition = item["condition"] if "condition" in item else "NM"
        tcg_id = item.get("tcg_id")

        if tcg_id is None:
            # Not provided
            continue
        else:
            # TCG ID is given, just figure out the market price
            cursor.execute(f"SELECT tcg_id, {CONDITION_MATRIX.get(condition)} FROM pokemon WHERE tcg_id = %s", (tcg_id,))
        results = cursor.fetchall()
        if len(results) != 1:
            # inconclusive result
            continue
        result = results[0]
        items.append((result[0], result[1]))

    string = "TCGplayer Id,,,,,,,,,,,,,Add to Quantity,TCG Marketplace Price\n"
    for item in items:
        string += f"{item[0]},,,,,,,,,,,,,1,{int(item[1]) / 100},\n"
    MYSQL.close()
    return flask.Response(bytes(string, "utf-8"), content_type="text/csv")