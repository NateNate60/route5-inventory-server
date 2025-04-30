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
        - If it's a sealed product, the description is ignored because it will automatically populate from the database.
    - `condition` (`str`): The item's condition.
        - For raw cards, either `nm`, `lp`, `mp`, `hp`, or `d`
        - For graded cards, use the grader and the grade, e.g. `PSA 10` or `CGC 9.5`.
        - **Note**: For CGC Pristine 10s, use `CGC PRISTINE`. For CGC Perfect 10s, use `CGC PERFECT`. For BGS Black Labels, use `BGS BLACK`.
    - `acquired_price` (`int`): The price paid for this item, in cents, per unit.
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

#### Request body

An array of objects with the following data:

- `id` (`int`): The asset tag, UPC, cert number of the item to be removed.
- `price` (`int`): The total price received for the item, in cents. If a trade was conducted, enter the amount of trade credit given.

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

### GET `/v1/inventory/consign`

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
- `consign_price` (`int`): The price of this item, in cents, per unit.
- `quantity` (`int`): The number of units of this product acquired. This parameter is ignored if `type` isn't `sealed`.
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
    "acquired_date": "2025-04-29",
    "acquired_txid": "TXB0001",
    "quantity": 0,
    "sale_date": "2025-04-30",
    "sale_txid": "TXS0002",
    "sale_price": 45000,
    "sale_price_changed_date": "2025-04-29",
    "consignor_name": "",
    "consignor_contact": ""
}
```

**Note**: The parameters `sale_date`, `sale_txid`, and `sale_price` are only present on raw cards which have been sold. The `quantity` parameter is the number of units of that product in stock and is only ever 1 or 0 for non-sealed products. Sealed products can have higher `quantity` values.

**Note**: `consignor_name` and `consignor_contact` will be the empty string for things that aren't on consignment.

#### Status codes

- 200 OK: The information was fetched successfully.
- 404 Not Found: The item scanned is not found in inventory.

### GET `/v1/transaction`

Get information about a transaction.

#### Request parameters

- `txid` (`str`): The ID of the transaction whose information to fetch.

#### Response

Data about the transaction, with the format depending on what sort of transaction is being inquired about.

For sale transactions (removing things from inventory):

```json
{
    "sale_date": "2025-04-29",
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
    "acquired_date": "2025-04-29",
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
    "consign_date": "2025-04-29",
    "consignor_name": "John Doe",
    "consignor_contact": "1234567890",
    "consign_price": 40000,
    "id": "A0001",
    "quantity": 1
}
```
