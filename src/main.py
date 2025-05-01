import flask
import pymongo
from datetime import datetime

import config
from authentication import authenticate

URI = f"mongodb+srv://{config.MONGODB_USERNAME}:{config.MONGODB_PASSWORD}@{config.MONGODB_CLUSTER}/?retryWrites=true&w=majority&appName={config.MONGODB_APPNAME}"
DATABASE = pymongo.MongoClient(URI, server_api=pymongo.server_api.ServerApi('1'))['route5']


app = flask.Flask(__name__)

@app.route("/v1/inventory/add", methods=["POST"])
def add_item ():
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
            result = DATABASE["inventory"].update_one({"id": item["id"]}, {"$inc": {"quantity": item["quantity"]}})
            # If nothing was modified, it's not in the database!
            if result.modified_count == 0:
                DATABASE["inventory"].insert_one(item)
        else:
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
    txid = "TXB" + f"{DATABASE['sales'].count_documents({})}".zfill(6)
    DATABASE["buys"].insert_one(
        {
            "acquired_date": datetime.today().strftime('%Y-%m-%d'),
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

    txid = txid = "TXC" + f"{DATABASE['sales'].count_documents({})}".zfill(6)
    DATABASE["consignments"].insert_one(
        {
            "consign_date": datetime.today().strftime('%Y-%m-%d'),
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
                "sale_date": datetime.today().strftime('%Y-%m-%d'),
                "sale_price": price
            }
        })
    txid = "TXS" + f"{DATABASE['sales'].count_documents({})}".zfill(6)
    DATABASE["sales"].insert_one(
        {
            "sale_date": datetime.today().strftime('%Y-%m-%d'),
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