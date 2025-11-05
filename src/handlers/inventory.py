import flask
import datetime
import tcgplayer
from database import get_db
from flask_jwt_extended import jwt_required, get_jwt

inventory = flask.Blueprint('inventory', __name__)

@inventory.route("/v1/inventory/add", methods=["POST"])
@jwt_required()
def add_item ():
    claims = get_jwt()
    DATABASE = get_db(claims["org"])
    data = flask.request.get_json()
    items = []
    price_total = 0
    for item in data["items"]:

        # Don't process entries with invalid quantity
        if item["quantity"] < 1:
            continue

        # If a tcgplayer ID is provided, fetch info from the database instead
        if "tcg_id" in item:
            card = tcgplayer.card_database_by_id(item["tcg_id"])
            item["description"] = card.card_name
            if item["type"] == "sealed":
                # Add this UPC to the card database
                tcgplayer.associate_upc(item["tcg_id"], item["id"])

        item["acquired_date"] = datetime.datetime.now(datetime.timezone.utc)
        item["consignor_name"] = ""
        item["consignor_contact"] = ""
        if item["type"] not in ("card", "slab", "sealed"):
            return flask.Response(
                {
                    "error": "Invalid item type"
                }, status=400
            )
        if item["type"] == "sealed":
            db_entry = DATABASE["inventory"].find_one({"id": item["id"]})

            if db_entry is None:
                # not in the database, so insert it
                item["sale_price_date"] = datetime.datetime.now(datetime.timezone.utc)
                DATABASE["inventory"].insert_one(item)
            else :
                # Determine new average cost basis
                previous_cost_basis = db_entry["acquired_price"] * db_entry["quantity"]
                new_cost_basis = previous_cost_basis + (item["quantity"] * item["acquired_price"])
                new_cost_basis_per_unit = new_cost_basis / (item["quantity"] + db_entry["quantity"])

                # Increment the number of this sealed product in inventory
                DATABASE["inventory"].update_one({"id": item["id"]}, {
                    "$inc": {"quantity": item["quantity"]},
                    "$set": {
                        "acquired_price": new_cost_basis_per_unit,
                        "sale_price": item["sale_price"],
                        "sale_price_date": datetime.datetime.now(datetime.timezone.utc)
                    }
                })
                
            
        else:
            item["sale_price_date"] = datetime.datetime.now(datetime.timezone.utc)
            item["quantity"] = 1
            if item["id"][0] != "B":
                DATABASE["inventory"].replace_one({"id": item["id"]}, 
                                                    replacement=item,
                                                    upsert=True)
            item["quantity"] = 1
        items.append({
            "id": item["id"],
            "description": item["description"],
            "acquired_price": item["acquired_price"],
            "sale_price": item["sale_price"],
            "quantity": item["quantity"]
        })
        price_total += item["acquired_price"] * item["quantity"]
    txid = "TXB" + f"{DATABASE['buys'].count_documents({})}".zfill(6)
    DATABASE["buys"].insert_one(
        {
            "acquired_date": datetime.datetime.now(datetime.timezone.utc),
            "acquired_from_name": data["acquired_from_name"],
            "acquired_from_contact": data["acquired_from_contact"],
            "credit_given": data["credit_given"] if "credit_given" in data else 0,
            "acquired_price_total": price_total,
            "payment_method": data["payment_method"] if "payment_method" in data else "unknown",
            "bulk_total": data["bulk_total"] if "bulk_total" in data else 0,
            "items": items,
            "txid": txid
        }
    )

    return {"txid": txid}

@inventory.route("/v1/inventory/prices", methods=["PATCH"])
@jwt_required()
def change_prices ():
    claims = get_jwt()
    DATABASE = get_db(claims["org"])
    if "id" not in flask.request.args or "price" not in flask.request.args:
        return flask.Response({"error": "Invalid parameters"}, status=400)

    try:
        price = flask.request.args.get('price')
        price = int(price)
    except ValueError:
        return flask.Response({"error": "Invalid parameters"}, status=400)
    
    result = DATABASE["inventory"].update_one({"id": flask.request.args.get("id")},
                                              {"$set": {"sale_price": price,
                                                        "sale_price_date": datetime.datetime.now(datetime.timezone.utc)
                                                        }
                                              })
    
    if result.modified_count == 0:
        return flask.Response({"error": "Inventory item not found"}, status=404)
    return {}

@inventory.route("/v1/inventory/consign", methods=["POST"])
@jwt_required()
def consign_item ():
    claims = get_jwt()
    DATABASE = get_db(claims["org"])
    item = flask.request.get_json()
    if item["type"] not in ("card", "slab", "sealed"):
        return flask.Response(
            {
                "error": "Invalid item type"
            }, status=400
        )
    if len(item["id"]) == 12 or (len(item['id']) == 13 and item[id][0] != '1'):
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
            "consign_date": datetime.datetime.now(datetime.timezone.utc),
            "consignor_name": item["consignor_name"],
            "consignor_contact": item["consignor_contact"],
            "sale_price": item["sale_price"],
            "item": item["id"],
            "txid": txid,
            "consignment_status": "unsold"
        }
    )

    return {"txid": txid}

@inventory.route("/v1/inventory/sell", methods=["POST"])
@jwt_required()
def sell_item ():
    claims = get_jwt()
    DATABASE = get_db(claims["org"])
    json = flask.request.get_json()
    payment_method = json["payment_method"]
    credit_applied = int(json["credit_applied"]) if "credit_applied" in json else 0
    bulk_total = 0
    items = json["items"]
    total_price = 0
    consignments = []

    processed_items = []
    for item in items:
        id = item["id"]
        price = item["sale_price"]
        if id[0] != "B":
            db_item = DATABASE["inventory"].find_one({"id": id})
            if db_item is None:
                return flask.Response({
                    "error": f"Item with ID {id} not found"
                }, status=404)

            if db_item["type"] != "sealed" or "quantity" not in item or item["quantity"] < 1:
                item["quantity"] = 1

            if db_item["quantity"] < item["quantity"]:
                # not enough items in stock to sell this quantity
                return flask.Response({
                    "error": f"Item ID {id} is out of stock"
                }, status=404)
            
            if db_item["consignor_name"] != "" and db_item["consignor_contact"] != "":
                # Item is a consignment item and consignor must be paid
                consignments.append(db_item["id"])
            
            item["acquired_price"] = db_item["acquired_price"]
            item["description"] = db_item["description"]
        else:
            bulk_total += price * item["quantity"]
            item["acquired_price"] = None
        total_price += price * item["quantity"]
        processed_items.append(item)
    for item in processed_items:

        # Skip bulk
        if item["id"][0] == "B":
            continue

        # If the item is sealed product don't set the price of the 
        # remaining units to be the price this unit was sold at.
        set_data = {"sale_date": datetime.datetime.now(datetime.timezone.utc)}
        if len(item['id']) != 12 and not (len(item['id']) == 13 and item['id'][0] == '1'):
            # It's not sealed product if the ID isn't a 12-digit UPC or EAN-13
            # Foreign products have an EAN-13 which generally will not begin with a 1
            set_data["sale_price"] = price

        DATABASE["inventory"].update_one({"id": item["id"]},  {
            "$inc": {"quantity": item["quantity"] * -1},
            "$set": set_data
        })
    txid = "TXS" + f"{DATABASE['sales'].count_documents({})}".zfill(6)
    DATABASE["sales"].insert_one(
        {
            "sale_date": datetime.datetime.now(datetime.timezone.utc),
            "sale_price_total": total_price,
            "credit_applied": credit_applied,
            "payment_method": payment_method,
            "bulk_total": bulk_total,
            "items": processed_items,
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

@inventory.route("/v1/inventory/prices/stale", methods=["GET"])
@jwt_required()
def get_stale_prices ():
    claims = get_jwt()
    DATABASE = get_db(claims["org"])
    cursor = DATABASE["inventory"].find({
        "sale_price_date": {"$lt": datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=7)},
        "quantity": {"$gt": 0}
    })

    r = []
    # Convert to a list so that it can be sent to caller
    for item in cursor:
        item.pop('_id')
        item['sale_price_date'] = item['sale_price_date'].isoformat() + "Z" if item['sale_price_date'] != "" else ""
        r.append(item)
    return r

@inventory.route("/v1/inventory/all", methods=["GET"])
@jwt_required()
def get_all_inventory ():
    claims = get_jwt()
    DATABASE = get_db(claims["org"])

    r = []

    # Find everything
    cursor = DATABASE["inventory"].find({"quantity": {"$gt": 0}})

    for item in cursor:
        item.pop('_id')

        if item["type"] == "sealed":
            result = tcgplayer.search_sealed_database(item["id"], True)
            if len(result) == 1:
                sealed = result[0]
                item["tcg_price_data"] = {
                    "tcgID": sealed.tcg_id,
                    "canonicalName": sealed.item_name,
                    "setName": sealed.set_name,
                    "attribute": "",
                    "priceData": {
                        "sealedMarketPrice": sealed.sealed_market_price,
                        "sealedLowPrice": sealed.sealed_low_price
                    }
                }
        elif item["type"] == "card":
            if "tcg_price_data" in item:
                # tcgID is known
                card = tcgplayer.card_database_by_id(item["tcg_price_data"]["tcgID"])
            else:
                result = tcgplayer.search_card_database(item["description"])
                if len(result) == 1:
                    card = result[0]
                    item["tcg_price_data"] = {
                        "tcgID": card.tcg_id,
                        "canonicalName": card.card_name,
                        "setName": card.set_name,
                        "attribute": card.attribute
                    }
                else:
                    card = None
            if type(card) is tcgplayer.Card:
                item["tcg_price_data"]["priceData"] = {
                    "nmMarketPrice": card.nm_market_price,
                    "lpMarketPrice": card.lp_market_price,
                    "mpMarketPrice": card.mp_market_price,
                    "hpMarketPrice": card.hp_market_price,
                    "dmMarketPrice": card.dm_market_price
                }

        item['acquired_date'] = item['acquired_date'].isoformat() + "Z"
        item['sale_price_date'] = item['sale_price_date'].isoformat() + "Z" if item['sale_price_date'] != "" else ""
        r.append(item)

    return r

@inventory.route("/v1/inventory", methods=["GET"])
@jwt_required()
def get_inventory_info ():
    claims = get_jwt()
    DATABASE = get_db(claims["org"])

    id = flask.request.args.get("id")
    if id == None:
        return flask.Response('{"error": "No item ID provided"}', status=400)
    
    item = DATABASE["inventory"].find_one({"id": id})

    if item == None:
        return flask.Response('{"error": "Item ID not found"}', status=404)
    item.pop("_id", None)
    if item["type"] == "sealed":
        sealed = tcgplayer.search_sealed_database(item["id"], True)
        if len(sealed) > 0:
            sealed = sealed[0]
            item["tcg_price_data"] = {
                "tcgID": sealed.tcg_id,
                "canonicalName": sealed.item_name,
                "setName": sealed.set_name,
                "attribute": "",
                "priceData": {
                    "sealedMarketPrice": sealed.sealed_market_price,
                    "sealedLowPrice": sealed.sealed_low_price
                }
            }
        
    elif item["type"] == "card":
        if "tcg_price_data" in item:
            # tcgID is known
            card = tcgplayer.card_database_by_id(item["tcg_price_data"]["tcgID"])
        else:
            result = tcgplayer.search_card_database(item["description"])
            if len(result) != 0:
                card = result[0]
                item["tcg_price_data"] = {
                    "tcgID": card.tcg_id,
                    "canonicalName": card.card_name,
                    "setName": card.set_name,
                    "attribute": card.attribute
                }
            else:
                card = None
        if type(card) is tcgplayer.Card:
            item["tcg_price_data"]["priceData"] = {
                "nmMarketPrice": card.nm_market_price,
                "lpMarketPrice": card.lp_market_price,
                "mpMarketPrice": card.mp_market_price,
                "hpMarketPrice": card.hp_market_price,
                "dmMarketPrice": card.dm_market_price
            }


    item['sale_price_date'] = item['sale_price_date'].isoformat() + "Z" if item['sale_price_date'] != "" else ""
    item['sale_date'] = item['sale_date'].isoformat() + 'Z' if item['sale_date'] != "" else ""
    item['acquired_date'] = item['acquired_date'].isoformat() + 'Z'
    return item
