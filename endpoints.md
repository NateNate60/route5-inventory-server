# Endpoints

This page lists the API endpoints for the Route 5 inventory management server and how to interact with them.


## Authentication

Authentication is by bearer tokens. Tokens are issued ahead of time. There is currently not a way to issue them through the API themselves. But once you have a token, include it in an `Authorization` header in the standard way, i.e. `Bearer [your bearer token]`.

## Re-use of asset tags

If an asset tag is added to inventory that already represents something else, the existing data is overwritten.

## Endpoints

### POST `/v1/inventory/add`

Add one or more items to the inventory.

#### Request body

An object with the following data:

- `items`: An array of objects with the following data:
    - `id` (`str`): The asset tag, UPC, or cert number of the item
    - `type` (`str`): Either `card`, `slab`, or `sealed`.
    - `description` (`str`): A description of the item.
        - If it's a card or slab, use the card's full canonical name followed by its collector number (e.g. `Umbreon VMAX 215`).
        - If the card is from a set that has 1st edition/unlimited variants, comes in holo and non-holo variants, or is from a set like XY Evolutions or Celebrations Classic Collection add that to the beginning, such as `Celebrations Charizard 4` or `Shadowless 1st Edition Charizard 4`.
        - If it's a sealed product, the description is ignored because it will automatically populate from the database.
    - `condition` (`str`): The item's condition.
        - For raw cards, either `nm`, `lp`, `mp`, `hp`, or `d`
        - For graded cards, use the grader and the grade, e.g. `PSA 10` or `CGC 9.5`.
        - **Note**: For CGC Pristine 10s, use `CGC PRISTINE`. For CGC Perfect 10s, use `CGC PERFECT`. For BGS Black Labels, use `BGS BLACK`.
        - For saled products, enter either `sealed` or `damaged` if the physical cling wrap is damaged.
    - `acquired_price` (`int`): The price paid for this item, in cents, per unit.
    - `sale_price` (`int`): The price at which this item is available for sale, in cents, per unit.
    - `quantity` (`int`): The number of units of this product acquired. This parameter is ignored if `type` isn't `sealed`.
- `acquired_from_name` (optional, `str`): The name of the person from whom these items were acquired.
- `acquired_from_contact` (optional, `str`): The telephone number or e-mail address of the person from whom these items were acquired.

#### Response

A JSON with the transaction ID.

```json
{
    "txid": "TXB0051"
}
```

#### Status codes

- 200 OK: The transaction was logged successfully.
- 400 Bad Request: The data is malformed.

**Note**: These transaction IDs always begin with `TXB`.

### POST `/v1/inventory/remove`

Remove one or more items to the inventory.

If an item is sold for a price other than its sale price, the records will be updated to reflect the new sale price. The exception to this is sealed product. Prices on sealed product will not be updated even if they are recorded as having been sold for a lower price.

#### Request body

An array of objects with the following data:

- `id` (`int`): The asset tag, UPC, cert number of the item to be removed.
- `sale_price` (`int`): The total price received for the item, in cents. If a trade was conducted, enter the amount of trade credit given.
- `quantity` (optional, `int`): The quantity of the sealed product sold. Ignored if the product isn't a sealed product. Defaults to 1.

#### Response

A JSON with the transaction ID.

```json
{
    "txid": "TXS0091"
}
```

**Note**: These transaction IDs always begin with `TXS`.

#### Status codes

- 200 OK: The transaction was logged successfully.
- 404 Not Found: One or more items scanned is not in inventory.

### POST `/v1/inventory/consign`

List a product as on consignment.

#### Request parameters

- `id` (`str`): The asset tag or cert number of the item.
- `type` (`str`): Either `card`, `slab`, or `sealed`.
- `description` (`str`): A description of the item.
    - If it's a card or slab, use the card's full canonical name followed by its collector number (e.g. `Umbreon VMAX 215`).
    - If it's a sealed product, the description is ignored because it will automatically populate from the database.
- `condition` (`str`): The item's condition.
    - For raw cards, either `nm`, `lp`, `mp`, `hp`, or `d`
    - For graded cards, use the grader and the grade, e.g. `PSA 10` or `CGC 9.5`.
    - **Note**: For CGC Pristine 10s, use `CGC PRISTINE`. For CGC Perfect 10s, use `CGC PERFECT`. For BGS Black Labels, use `BGS BLACK`.
- `sale_price` (`int`): The price at which this item should be sold, in cents, per unit.
- `consignor_name` (`str`): The name of the consignor of this item.
- `consignor_contact` (`str`): The telephone number or email of the consignor of this item.

**Note**: The ID cannot be a UPC. UPCs will be rejected. Use an asset tag instead.

#### Response

A JSON object in the following format:

```json
{
    "txid": "TXC0001"
}
```

**Note**: These transaction IDs always begin with `TXC`.

#### Status codes

- 201 Created: The record has been added successfully.
- 400 Bad Request: The data is malformed.

### GET `/v1/inventory`

Get information about an item in inventory.

#### Request parameters

- `id` (`str`): The asset tag, UPC, or cert number of the item.

#### Response

Data about the item in the following format:

```json
{
    "id": "A1234",
    "type": "slab",
    "description": "UMBREON V 189",
    "condition": "PSA 10",
    "acquired_price": 40000,
    "acquired_date": "2025-05-02T19:09:15.320Z",
    "acquired_txid": "TXB0001",
    "quantity": 0,
    "sale_date": "2025-05-10T18:23:46.622000Z",
    "sale_txid": "TXS0002",
    "sale_price": 45000,
    "sale_price_changed_date": "2025-05-02T19:09:15.320Z",
    "consignor_name": "",
    "consignor_contact": ""
}
```

**Note**: The parameters `sale_date` and `sale_txid` are only present on raw cards which have been sold. The `quantity` parameter is the number of units of that product in stock and is only ever 1 or 0 for non-sealed products. Sealed products can have higher `quantity` values.

**Note**: `consignor_name` and `consignor_contact` will be the empty string for things that aren't on consignment.

#### Status codes

- 200 OK: The information was fetched successfully.
- 404 Not Found: The item scanned is not found in inventory.

### GET `/v1/inventory/prices/stale`

Fetch a list of things whose prices are stale (priced more than 7 days ago)

#### Request parameters

No parameters are required.

#### Response

A JSON list of in-stock inventory items whose prices were last updated more than 7 days ago.

**Example:**
```json
[
    {
        "id": "A00001",
        "type": "card",
        "description": "Umbreon VMAX 215",
        "condition": "nm",
        "acquired_price": 90000,
        "sale_price": 120000,
        "sale_price_date": "2024-05-02T19:04:35.735Z",
        "quantity": 1,
        "consignor": "",
        "consignor_contact": ""
    },
    {
        "id": "A00002",
        "type": "card",
        "description": "Celebrations Charizard 4",
        "condition": "nm",
        "acquired_price": 9000,
        "sale_price": 100000,
        "sale_price_date": "2025-05-02T19:09:15.320Z",
        "quantity": 1,
        "consignor": "",
        "consignor_contact": ""
    }
]
```

### PATCH `/v1/inventory/prices`

Update the price of an item.

Prices of items that are out of stock can still be changed by calling this endpoint.

#### Request parameters

- `id` (`str`): The serial number, UPC, or asset tag of the item whose price to change.
- `price` (`int`): The new price of the item, in cents.

#### Status codes

- 200 OK: The price was successfully updated.
- 404 Not Found: The item with the given ID was not found in inventory.

### GET `/v1/inventory/all`

Get a list of everything in the inventory where there is at least 1 unit in stock.

#### Requires parameters

None

#### Response

A JSON list of things in the inventory, in the following format:

```json
[
    {
        "acquired_price": 300,
        "condition": "NM",
        "consignor_contact": "",
        "consignor_name": "",
        "description": "Probopass 182",
        "id": "A0030",
        "quantity": 1,
        "sale_date": "",
        "sale_price": 170,
        "sale_price_date": "2025-05-10T16:23:46.622000Z",
        "type": "card"
    }
]
```


### GET `/v1/transaction`

Get information about a transaction.

#### Request parameters

- `txid` (`str`): The ID of the transaction whose information to fetch.

#### Response

Data about the transaction, with the format depending on what sort of transaction is being inquired about.

For sale transactions (removing things from inventory):

```json
{
    "sale_date": "2025-05-02T19:09:15.320Z",
    "sale_total": 50000,
    "sale_items": [
        {
            "id": "A0001",
            "sale_price": 1000,
            "quantity": 1
        },
        {
            "id": "104691943",
            "sale_price": 49000,
            "quantity": 1
        },
        {
            "id": "196214108202",
            "sale_price": 20000,
            "quantity": 2
        }
    ]
}
```

For purchase transactions (adding things to inventory):

```json
{
    "acquired_date": "2025-04-02T04:09:15.320Z",
    "acquired_from_name": "John Doe",
    "acquired_from_contact": "1234567890",
    "acquired_price_total": 40000,
    "items": [
        {
            "id": "A0001",
            "acquired_price": 5000,
            "quantity": 1
        },
        {
            "id": "196214108202",
            "acquired_price": 20000,
            "quantity": 2
        }
    ]
}
```

For consignment transactions:

```json
{
    "consign_date": "2025-05-02T01:09:15.320Z",
    "consignor_name": "John Doe",
    "consignor_contact": "1234567890",
    "sale_price": 40000,
    "item": "A0001",
    "txid": 1,
    "consignment_status": "sold"
}
```

**Note**: The possible consignment statuses are:
- `unsold`, meaning the product has not yet been sold.
- `sold`, meaning the product has been sold but the consignor hasn't been paid yet.
- `complete`, meaning the product has been sold and the consignor has been paid.
- `hold`, meaning something else applies to the consignment product.

### GET `/v1/psa`

Look up a PSA slab's cert number using the PSA cert lookup.

#### Request parameters

- `id` (`string`): The slab's cert number

#### Response

JSON data in the following form

```json
{
    "cert": "113426540",
    "grade": "10",
    "grader": "PSA",
    "name": "SWORD & SHIELD EVOLVING SKIES 218 FULL ART/RAYQUAZA VMAX SECRET"
}
```

**Warning**: PSA API rate limits only allow 100 queries per day without payment.