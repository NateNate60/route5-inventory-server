import flask
import datetime
import tcgplayer
import config
from database import get_db
from flask_jwt_extended import jwt_required, get_jwt

inventory = flask.Blueprint('inventory', __name__)

@inventory.route("/v1/inventory/add", methods=["POST"])
@jwt_required()
def add_item ():
    claims = get_jwt()
    data = flask.request.get_json()
    items = []
    price_total = 0
    
    # Data validation

    if type(data.get("credit_given")) not in (int, float):
        return flask.Response({"error": "Missing credit_given"}, status=400)
    for item in data['items']:
        if (type(item.get("acquired_price")) not in (int, float) or
            type(item.get("quantity")) is not int or
            type(item.get("description")) is not str or
            type(item.get("type")) is not str or
            type(item.get("condition")) is not str or
            type(item.get("id")) not in (int, str) or
            type(item.get("sale_price")) not in (int, float)):

            return flask.Response({"error": "Items missing one or more required fields"}, status=400)
        
        if item["type"] not in ("card", "slab", "sealed"):
            return flask.Response({"error": "Invalid item type"}, status=400)
        price_total += item["acquired_price"] * item["quantity"]
    
    MYSQL = get_db()
    
    cursor = MYSQL.cursor()
    cursor.execute("INSERT INTO Buys VALUES (%s, %s, NULL, NOW(), %s, %s, %s)", (
        claims['org'],
        claims['username'],
        price_total,
        data['credit_given'],
        data['payment_method'] if data.get('payment_method') is not None else "cash"
    ))
    MYSQL.commit()
    txid = cursor.lastrowid
    for item in data["items"]:

        # Don't process entries with invalid quantity
        if item["quantity"] < 1:
            continue

        # If a tcgplayer ID is provided, fetch info from the database instead
        if "tcg_price_data" in item and item['type'] == "card":
            card = tcgplayer.card_database_by_id(item["tcg_price_data"]["tcgID"])
            item["description"] = card.card_name
        if item["type"] == "sealed" and item.get("upc"):
            # Add this UPC to the card database
            tcgplayer.associate_upc(item["id"], item["upc"])

        item["acquired_date"] = datetime.datetime.now(datetime.timezone.utc)
        item["consignor_name"] = ""
        item["consignor_contact"] = ""
        tcg_id = None
        if "tcg_price_data" in item:
            tcg_id = item["tcg_price_data"]["tcgID"]
        market_price = item.get('market_price')
        if item["type"] == "sealed":
            cursor.execute("SELECT acquired_price, quantity FROM Inventory WHERE item_id = %s AND org = %s", (
                item['id'],
                claims['org']
            ))
            results = cursor.fetchall()
            if len(results) == 0:
                # Not in inventory, so insert it
                cursor.execute("INSERT INTO Inventory VALUES (%s, 'sealed', %s, %s, NOW(), %s, %s, %s, %s, %s)", (
                    item['id'],
                    item["description"],
                    tcg_id,
                    item["acquired_price"],
                    item["sale_price"],
                    item["condition"],
                    item["quantity"],
                    claims["org"]
                ))
                MYSQL.commit()
            else:
                result = results[0]
                new_cost_basis = ((result[0] * result[1]) + (item['acquired_price'] * item['quantity'])) / (result[1] + item['quantity'])
                cursor.execute("UPDATE Inventory SET quantity = quantity + %s, acquired_price = %s, acquired_date = NOW() " \
                               "WHERE item_id = %s AND org = %s", (
                                   item['quantity'],
                                   new_cost_basis,
                                   item['id'],
                                   claims['org']
                               ))
                MYSQL.commit()
        else:
            item["quantity"] = 1
            if item["id"][0] != "B":
                cursor.execute("INSERT INTO Inventory VALUES (%s, %s, %s, %s, NOW(), %s, %s, %s, %s, %s)", (
                    item["id"],
                    item["type"],
                    item["description"],
                    tcg_id,
                    item["acquired_price"],
                    item["sale_price"],
                    item["condition"],
                    item["quantity"],
                    claims['org']
                ))
                MYSQL.commit()
        cursor.execute("INSERT INTO BuyTxRow VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", (
            txid,
            item["id"],
            item["description"],
            item["acquired_price"],
            item.get("sale_price"),
            item["quantity"],
            item["condition"],
            item.get("tcg_id")
        ))
        MYSQL.commit()
    cursor.close()
    MYSQL.close()

    return {"txid": txid}

@inventory.route("/v1/inventory/prices", methods=["PATCH"])
@jwt_required()
def change_prices ():
    claims = get_jwt()
    if "id" not in flask.request.args or "price" not in flask.request.args:
        return flask.Response({"error": "Invalid parameters"}, status=400)

    try:
        price = flask.request.args.get('price')
        price = int(price)
    except ValueError:
        return flask.Response({"error": "Invalid parameters"}, status=400)
    
    MYSQL = get_db()
    cursor = MYSQL.cursor()
    cursor.execute("UPDATE Inventory SET sale_price = %s WHERE item_id = %s AND org = %s", (
        price,
        flask.request.args.get["id"],
        claims['org']
    ))
    MYSQL.commit()
    
    if cursor.rowcount == 0:
        return flask.Response({"error": "Inventory item not found"}, status=404)
    return {}

@inventory.route("/v1/inventory/consign", methods=["POST"])
@jwt_required()
def consign_item ():
    return flask.Response({"error": "Unimplemented"}, status=501)

@inventory.route("/v1/inventory/sell", methods=["POST"])
@jwt_required()
def sell_item ():
    claims = get_jwt()
    data = flask.request.get_json()

    payment_method = data.get("payment_method") if data.get("payment_method") is not None else "cash"
    credit_applied = float(data["credit_applied"]) if "credit_applied" in data else 0
    items = data["items"]
    total_price = 0

    MYSQL = get_db()
    cursor = MYSQL.cursor()

    # Data validation
    for item in items:
        if (type(item.get("id")) is not str or
            type(item.get("sale_price")) not in (int, float) or
            type(item.get("quantity")) is not int):

            cursor.close()
            MYSQL.close()
            return flask.Response({"error": "Items missing one or more required fields"})
        if item['id'][0] != "B":
            cursor.execute("SELECT Inventory.item_type FROM Inventory LEFT JOIN upc ON upc.tcg_id = Inventory.tcg_id " \
                           "WHERE org = %s AND (Inventory.item_id = %s OR upc.upc = %s) AND quantity >= %s", (
                    claims['org'],
                    item['id'],
                    item['id'],
                    item['quantity']
                ))
            results = cursor.fetchall()
            if len(results) != 1:
                cursor.close()
                MYSQL.close()
                return flask.Response({
                    "error": f"Not enough of item with ID {id} in stock"
                }, status=404)
        total_price += item["sale_price"] * item["quantity"]
   
    cursor.execute("UPDATE Inventory SET quantity = quantity - %s WHERE org = %s AND item_id = %s", (
        item['quantity'],
        claims['org'],
        item['id']
    ))
    MYSQL.commit()

    cursor.execute("INSERT INTO Sales VALUES (%s, %s, NULL, NOW(), %s, %s, %s)", (
        claims["org"],
        claims["username"],
        total_price,
        credit_applied,
        payment_method
    ))
    MYSQL.commit()
    txid = cursor.lastrowid

    for item in items:
        if item['id'][0] == 'B':
            cursor.execute("INSERT INTO SellTxRow VALUES (%s, %s, %s, %s, %s, NULL, %s)", (
                txid,
                item['id'],
                item['description'],
                item['sale_price'],
                item['quantity'],
                item.get('tcg_id')
            ))
            MYSQL.commit()
        else:
            cursor.execute("INSERT INTO SellTxRow VALUES (%s, %s, %s, %s, %s, (SELECT acquired_price FROM Inventory WHERE org = %s AND item_id = %s), %s)", (
                    txid,
                    item['id'],
                    item['description'],
                    item['sale_price'],
                    item['quantity'],
                    claims['org'],
                    item['id'],
                    item.get('tcg_id')
                ))
            MYSQL.commit()

    return {"txid": txid}

@inventory.route("/v1/inventory/prices/stale", methods=["GET"])
@jwt_required()
def get_stale_prices ():
    return flask.Response({"error": "Unimplemented"}, status=501) 

@inventory.route("/v1/inventory/all", methods=["GET"])
@jwt_required()
def get_all_inventory ():
    claims = get_jwt()
    MYSQL = get_db()

    r = []

    # Find everything
    cursor = MYSQL.cursor(buffered=True)
    cursor.execute("SELECT * FROM Inventory WHERE org = %s AND quantity != 0", (
        claims['org'],
    ))
    results = cursor.fetchall()

    i = 0
    for result in results:
        i += 1
        print(i, end='\r')
        item = {
            "id": result[0],
            "type": result[1],
            "description": result[2],
            "tcg_id": result[3],
            "acquired_date": result[4],
            "acquired_price": result[5],
            "sale_price": result[6],
            "condition": result[7],
            "quantity": result[8]
        }

        if item["type"] == "sealed":
            cursor.execute("SELECT sealed.tcg_id, sealed.set_name, sealed.item_name, sealed.sealed_market_price, sealed.sealed_low_price, photo_url, upc.upc " \
                           "FROM sealed LEFT JOIN upc ON upc.tcg_id = sealed.tcg_id " \
                           "WHERE sealed.tcg_id = %s;", (result[0],))
            result = cursor.fetchall()
            if len(result) >= 1:
                sealed = result[0]
                item["upc"] = sealed[6]
                item["tcg_price_data"] = {
                    "tcgID": sealed[0],
                    "canonicalName": sealed[2],
                    "setName": sealed[1],
                    "attribute": "",
                    "imageURL": sealed[5],
                    "priceData": {
                        "sealedMarketPrice": sealed[3],
                        "sealedLowPrice": sealed[4]
                    }
                }
        elif item["type"] == "card":
            if item["tcg_id"]:
                # TCG ID is known
                cursor.execute("SELECT * FROM pokemon WHERE tcg_id = %s", (item['tcg_id'],))
                data = cursor.fetchone()
                item["tcg_price_data"] = {
                    "tcgID": data[0],
                    "canonicalName": data[2],
                    "setName": data[1],
                    "priceData": {
                        "nmMarketPrice": data[4],
                        "lpMarketPrice": data[5],
                        "mpMarketPrice": data[6],
                        "hpMarketPrice": data[7],
                        "dmMarketPrice": data[8],
                        "nmLowPrice": data[9],
                        "lpLowPrice": data[10],
                        "mpLowPrice": data[11],
                        "hpLowPrice": data[12],
                        "dmLowPrice": data[13],
                    },
                    "attribute": data[14],
                    "imageURL": data[15]
                }

        item['acquired_date'] = item['acquired_date'].timestamp()
        r.append(item)

    return r

@inventory.route("/v1/inventory", methods=["GET"])
@jwt_required()
def get_inventory_info ():
    claims = get_jwt()

    id = flask.request.args.get("id")
    if id == None:
        return flask.Response('{"error": "No item ID provided"}', status=400)
    
    MYSQL = get_db()
    cursor = MYSQL.cursor()

    if len(id) in (12, 13, 7, 6):
        if len(id) <= 7:
            cursor.execute("SELECT * FROM Inventory " \
                        "LEFT JOIN upc ON Inventory.tcg_id = upc.tcg_id " \
                        "LEFT JOIN sealed ON sealed.tcg_id = Inventory.tcg_id WHERE Inventory.org = %s AND Inventory.tcg_id = %s", (claims['org'], id))
        else:
            cursor.execute("SELECT * FROM Inventory " \
                        "LEFT JOIN upc ON Inventory.tcg_id = upc.tcg_id " \
                        "LEFT JOIN sealed ON sealed.tcg_id = Inventory.tcg_id WHERE Inventory.org = %s AND upc.upc = %s", (claims['org'], id))
        results = cursor.fetchall()
        if len(results) == 1:
            result = results[0]
            if result[1] != "sealed":
                flask.Response('{"error": "Cannot search non-sealed product by TCG Player ID"}', status=422)
            item = {
                "id": result[0],
                "type": "sealed",
                "description": result[2],
                "tcg_id": result[3],
                "acquired_date": result[4],
                "acquired_price": result[5],
                "sale_price": result[6],
                "condition": "sealed",
                "quantity": result[8],
                "upc": result[11],
            }
            item["tcg_price_data"] = {
                "tcgID": result[0],
                "canonicalName": result[14],
                "setName": result[13],
                "imageURL": result[17],
                "upc": result[11],
                "attribute": "",
                "priceData": {
                    "sealedMarketPrice": result[15],
                    "sealedLowPrice": result[16]
                }
            }
        else:
            return flask.Response('{"error": "Item ID not found"}', status=404)
    else:
        cursor.execute("SELECT * FROM Inventory WHERE org = %s AND item_id = %s", (
            claims['org'],
            id
        ))
        results = cursor.fetchall()
        if len(results) != 1:
            return flask.Response('{"error": "Item ID not found"}', status=404)
        result = results[0]
        item = {
            "id": result[0],
            "type": result[1],
            "description": result[2],
            "tcg_id": result[3],
            "acquired_date": result[4],
            "acquired_price": result[5],
            "sale_price": result[6],
            "condition": result[7],
            "quantity": result[8],
        }
        if item['type'] == 'card':
            cursor.execute("SELECT * FROM pokemon WHERE tcg_id = %s", (item["tcg_id"],))
            results = cursor.fetchall()
            if len(results) != 0:
                result = results[0]
                item["tcg_price_data"] = {
                    "tcgID": result[0],
                    "setName": result[1],
                    "canonicalName": result[2],
                    "attribute": result[14],
                    "imageURL": result[15],
                    "number": result[3],
                    "priceData": {
                        "nmMarketPrice": result[4],
                        "lpMarketPrice": result[5],
                        "mpMarketPrice": result[6],
                        "hpMarketPrice": result[7],
                        "dmMarketPrice": result[8],
                        "nmLowPrice": result[9],
                        "lpLowPrice": result[10],
                        "mpLowPrice": result[11],
                        "hpLowPrice": result[12],
                        "dmLowPrice": result[13],
                    }
                }


    item['sale_price_date'] = item['sale_price_date'].timestamp() if item.get('sale_price_date') else ""
    item['sale_date'] = item['sale_date'].timestamp() if item.get('sale_date') else ""
    item['acquired_date'] = item['acquired_date'].timestamp() if item.get('acquired_date') else datetime.datetime.now().timestamp()
    return item
