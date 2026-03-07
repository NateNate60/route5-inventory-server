import flask
from flask_jwt_extended import get_jwt, jwt_required

from datetime import datetime
from mysql import connector

import config
from database import get_db

transactions = flask.Blueprint('transactions', __name__)

@transactions.route("/v1/transaction/buys")
@jwt_required()
def get_buy_transactions ():
    claims = get_jwt()

    # Validation
    try:
        start_date = int(flask.request.args.get("start_date"))
        end_date = int(flask.request.args.get("end_date"))
    except (ValueError, TypeError):
        return flask.Response({"error": "Invalid dates"}, status=400)

    MYSQL = get_db()
    cursor = MYSQL.cursor()
    cursor.execute("SELECT * FROM Buys WHERE org = %s AND acquired_date < FROM_UNIXTIME(%s) AND acquired_date > FROM_UNIXTIME(%s)", (
        claims['org'],
        end_date,
        start_date
    ))
    txs = cursor.fetchall()
    data = []
    
    for tx in txs:
        tx_data = {
            "username": tx[1],
            "txid": f"TXB{str(tx[2]).zfill(6)}",
            "acquired_date": tx[3].timestamp(),
            "acquired_price_total": tx[4],
            "credit_given": tx[5],
            "payment_method": tx[6],
            "items": []
        }
        cursor.execute("SELECT * FROM BuyTxRow WHERE txid = %s", (tx[2],))
        rows = cursor.fetchall()
        for row in rows:
            tx_data["items"].append({
                "id": row[1],
                "description": row[2],
                "acquired_price": row[3],
                "sale_price": row[4],
                "quantity": row[5],
                "condition": row[6],
                "tcg_id": row[7]
            })
        data.append(tx_data)
    return data

@transactions.route("/v1/transaction/sales")
@jwt_required()
def get_sale_transactions ():
    claims = get_jwt()

    # Validation
    try:
        start_date = int(flask.request.args.get("start_date"))
        end_date = int(flask.request.args.get("end_date"))
    except (ValueError, TypeError):
        return flask.Response({"error": "Invalid dates"}, status=400)

    MYSQL = get_db()
    cursor = MYSQL.cursor()
    cursor.execute("SELECT * FROM Sales WHERE org = %s AND sale_date < FROM_UNIXTIME(%s) AND sale_date > FROM_UNIXTIME(%s)", (
        claims['org'],
        end_date,
        start_date
    ))
    txs = cursor.fetchall()
    data = []
    
    for tx in txs:
        tx_data = {
            "username": tx[1],
            "txid": f"TXS{str(tx[2]).zfill(6)}",
            "sale_date": tx[3].timestamp(),
            "sale_price_total": tx[4],
            "credit_applied": tx[5],
            "payment_method": tx[6],
            "items": []
        }
        cursor.execute("SELECT * FROM SellTxRow WHERE txid = %s", (tx[2],))
        rows = cursor.fetchall()
        for row in rows:
            tx_data["items"].append({
                "id": row[1],
                "description": row[2],
                "acquired_price": row[5],
                "sale_price": row[3],
                "quantity": row[4],
            })
        data.append(tx_data)
    return data