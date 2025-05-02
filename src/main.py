import flask
import pymongo
from datetime import datetime, timedelta

import config
from authentication import authenticate

URI = f"mongodb+srv://{config.MONGODB_USERNAME}:{config.MONGODB_PASSWORD}@{config.MONGODB_CLUSTER}/?retryWrites=true&w=majority&appName={config.MONGODB_APPNAME}"
DATABASE = pymongo.MongoClient(URI, server_api=pymongo.server_api.ServerApi('1'))['route5']


app = flask.Flask(__name__)

@app.route("/v1/inventory/add", methods=["POST"])
def add_item ():
    user = authenticate(flask.request.headers.get("Authorization"))
    if user == "":
        return flask.Response({}, status=401)
    
    data = flask.request.get_json()
    items = []
    price_total = 0
    for item in data["items"]:
        item["consignor_name"] = ""
        item["consignor_contact"] = ""
        if item["type"] not in ("card", "slab", "sealed"):
            return flask.Response(
                {
                    "error": "Invalid item type"
                }, status=400
            )
        if item["type"] == "sealed":
            # Increment the number of this sealed product in inventory
            result = DATABASE["inventory"].update_one({"id": item["id"]}, {
                "$inc": {"quantity": item["quantity"]},
                "$set": {
                    "sale_price": item["sale_price"],
                    "sale_price_date": datetime.today()
                }
            })
            # If nothing was modified, it's not in the database!
            if result.modified_count == 0:
                item["sale_price_date"] = datetime.today()
                DATABASE["inventory"].insert_one(item)
        else:
            item["sale_price_date"] = datetime.today()
            item["quantity"] = 1
            result = DATABASE["inventory"].replace_one({"id": item["id"]}, 
                                                       replacement=item,
                                                       upsert=True)
            item["quantity"] = 1
        items.append({
            "id": item["id"],
            "acquired_price": item["acquired_price"],
            "quantity": item["quantity"]
        })
        price_total += item["acquired_price"]
    txid = "TXB" + f"{DATABASE['buys'].count_documents({})}".zfill(6)
    DATABASE["buys"].insert_one(
        {
            "acquired_date": datetime.today(),
            "acquired_from_name": data["acquired_from_name"],
            "acquired_from_contact": data["acquired_from_contact"],
            "acquired_price_total": price_total,
            "items": items,
            "txid": txid
        }
    )

    return {"txid": txid}

@app.route("/v1/inventory/consign", methods=["POST"])
def consign_item ():
    user = authenticate(flask.request.headers.get("Authorization"))
    if user == "":
        return flask.Response({}, status=401)
    
    item = flask.request.get_json()
    if item["type"] not in ("card", "slab", "sealed"):
        return flask.Response(
            {
                "error": "Invalid item type"
            }, status=400
        )
    if len(item["id"]) == 12:
        # This is a UPC and should be rejected
        return flask.Response(
            {
                "error": "No UPCs allowed"
            }, status=400
        ) 
    
    item["quantity"] = 1
    result = DATABASE["inventory"].replace_one(filter={"id": item["id"]}, 
                                                replacement=item,
                                                upsert=True)

    txid = txid = "TXC" + f"{DATABASE['consignments'].count_documents({})}".zfill(6)
    DATABASE["consignments"].insert_one(
        {
            "consign_date": datetime.today(),
            "consignor_name": item["consignor_name"],
            "consignor_contact": item["consignor_contact"],
            "sale_price": item["sale_price"],
            "item": item["id"],
            "txid": txid,
            "consignment_status": "unsold"
        }
    )

    return {"txid": txid}

@app.route("/v1/inventory/remove", methods=["POST"])
def sell_item ():
    user = authenticate(flask.request.headers.get("Authorization"))
    if user == "":
        return flask.Response({}, status=401)
    
    user = authenticate(flask.request.headers.get("Authorization"))
    if user == "":
        return flask.Response({}, status=401)
    
    items = flask.request.get_json()
    total_price = 0
    consignments = []
    for item in items:
        id = item["id"]
        price = item["sale_price"]
        db_item = DATABASE["inventory"].find_one({"id": id})
        if db_item is None:
            return flask.Response({
                "error": "Item with given ID not found"
            }, status=404)

        if db_item["type"] != "sealed" or "quantity" not in item or item["quantity"] < 1:
            item["quantity"] = 1

        if db_item["quantity"] < item["quantity"]:
            # not enough items in stock to sell this quantity
            return flask.Response({
                "error": "Item is out of stock"
            }, status=404)
        
        if db_item["consignor_name"] != "" and db_item["consignor_contact"] != "":
            # Item is a consignment item and consignor must be paid
            consignments.append(db_item["id"])

        total_price += price
    for item in items:
        DATABASE["inventory"].update_one({"id": item["id"]},  {
            "$inc": {"quantity": item["quantity"] * -1},
            "$set": {
                "sale_date": datetime.today(),
                "sale_price": price
            }
        })
    txid = "TXS" + f"{DATABASE['sales'].count_documents({})}".zfill(6)
    DATABASE["sales"].insert_one(
        {
            "sale_date": datetime.today(),
            "sale_price_total": total_price,
            "items": items,
            "txid": txid
        }
    )

    for item_id in consignments:
        # Record the sold consignments as complete.
        DATABASE["consignments"].update_one(
            {"item": item_id},
            {"$set": {"consignment_status": "sold"}}
        )
    return {"txid": txid}

@app.route("/v1/inventory", methods=["GET"])
def get_inventory_info ():
    user = authenticate(flask.request.headers.get("Authorization"))
    if user == "":
        return flask.Response({}, status=401)
    
    id = flask.request.args.get("id")
    if id == None:
        return flask.Response({"error": "No item ID provided"}, status=400)
    
    item = DATABASE["inventory"].find_one({"id": id})

    if item == None:
        return flask.Response({"error": "Item ID not found"}, status=404)
    item.pop("_id", None)
    return item

@app.route("/v1/transactions")
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

@app.route("/v1/inventory/prices/stale", methods=["GET"])
def get_stale_prices ():
    user = authenticate(flask.request.headers.get("Authorization"))
    if user == "":
        return flask.Response({}, status=401)
    
    cursor = DATABASE["inventory"].find({
        "sale_price_date": {"$lt" : datetime.today() - timedelta(days=7)},
        "quantity": {"$gt": 0}
    })

    r = []
    # Convert to a list so that it can be sent to caller
    for item in cursor:
        item.pop('_id')
        r.append(item)
    return r

@app.route("/v1/inventory/prices", methods=["PATCH"])
def change_prices ():
    user = authenticate(flask.request.headers.get("Authorization"))
    if user == "":
        return flask.Response({}, status=401)
    
    if "id" not in flask.request.args or "price" not in flask.request.args:
        return flask.Response({"error": "Invalid parameters"}, status=400)

    try:
        price = flask.request.args.get('price')
        price = int(price)
    except ValueError:
        return flask.Response({"error": "Invalid parameters"}, status=400)
    
    result = DATABASE["inventory"].update_one({"id": flask.request.args.get("id")},
                                              {"$set": {"sale_price": price,
                                                        "sale_price_date": datetime.today()
                                                        }
                                              })
    
    if result.modified_count == 0:
        return flask.Response({"error": "Inventory item not found"}, status=404)
    return {}