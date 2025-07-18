# Endpoints

This page lists the API endpoints for the Route 5 inventory management server and how to interact with them.


## Authentication

Authentication is by bearer tokens. Once you have a token, include it in an `Authorization` header in the standard way, i.e. `Bearer [your bearer token]`. All endpoints take access tokens except for `/v1/login` (which takes no tokens at all) and `/v1/login/tokens/access` (which takes a refresh token). Access tokens are good for 20 minutes. Refresh tokens are good for 30 days.

## Re-use of asset tags

If an asset tag is added to inventory that already represents something else, the existing data is overwritten.

## Endpoints

### POST `/v1/login`

Obtain a refresh token and an access token. The refresh token is good for 30 days. The access token is good for 20 minutes.

#### Request body

A JSON object with the following data:

- `username` (`str`): The username of the user to log in.
- `password` (`str`): The user's password.

#### Response

An object with the following data:

- `refresh_token` (`str`): A refresh token
- `access_token` (`str`): An access token

### POST `/v1/login/tokens/access`

Obtain an access token (using a refresh token). The access token is good for 20 minutes.

#### Request parameters

None required

#### Response

An object with the following data:

- `access_token` (`str`): An access token

### GET `/v1/login/tokens/access/validity`

Determine whether an access token is still good and return its username and expiration date.

#### Response

If the token is still good, this endpoint returns a JSON object with the following data:

- `username` (`str`): The username associated with the token.
- `expiration` (`str`): When the token expires, in ISO 8601 format.

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
- `credit_given` (optional, `int`): The amount of store credit given for this purchase
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

An object with the following data:

```json
{
    "credit_applied": 1234,
    "payment_method": "cash"
    "items": [
        {
            "id": "A0001",
            "sale_price": 2234,
            "quantity": 1
        }
    ]
}
```

- `credit_applied` (`int`) indicates that amount of store credit applied to the purchase (in cents).
- `payment_method` (`str`) is something like `venmo`, `zelle`, `cashapp`, `paypal`, `card`, or `cash` and indicates the method used by the customer to pay the remainder of the balance. Use `cash` if store credit was used to cover the entire purchase.
- `items` is an array of objects with the following properties:
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
    "sale_price_total": 50000,
    "payment_method": "cash",
    "credit_applied": 1000,
    "items": [
        {
            "id": "A0001",
            "sale_price": 1000,
            "quantity": 1,
            "acquired_price": 900,
            "description": "Card Name 123"
        },
        {
            "id": "104691943",
            "sale_price": 49000,
            "quantity": 1,
            "acquired_price": 40000,
            "description": "Card Name 123 PSA 10"
        },
        {
            "id": "196214108202",
            "sale_price": 20000,
            "quantity": 2,
            "acquired_price": 15000,
            "description": "Sealed Product Name"
        }
    ]
}
```

Note that `credit_applied` indicates the amount of store credit applied towards the transaction. The `sale_total` indicates the sum of all payments received, *inclusive of store credit*. So in the above example, this would indicate $490.00 in cash was paid, and $10.00 in store credit was applied, for a total sale of $500.00.

For purchase transactions (adding things to inventory):

```json
{
    "acquired_date": "2025-04-02T04:09:15.320Z",
    "acquired_from_name": "John Doe",
    "acquired_from_contact": "1234567890",
    "acquired_price_total": 40000,
    "credit_given": 30000
    "payment_method": "cash"
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

Note that `credit_applied` indicates the amount of store credit applied towards the transaction. The `acquired_price_total` indicates the sum of all payments received, *inclusive of store credit*. So in the above example, this would indicate $100.00 in cash was paid, and $300.00 in store credit was given, for a total payment of $400.00.

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

### POST `/v1/prices/update`

Update the TCG Player price database based on a CSV file obtained from the Pricing tab of the seller portal.

The CSV file can be obtained by going to the TCG Player seller portal Pricing tab, clicked "export filtered CSV", then selecting "Pokemon" or "Pokemon Japan" under Category. It is advised to untick "export only from live inventory" and to tick "do not compare against price".

Only admins can call this endpoint.

**Warning**: This endpoint will block until it has finished processing the CSV file, which could take a long time, especially because the CSV file is usually contains hundreds of thousands of entries. Therefore, it is recommended to call it asynchronously instead of awaiting it to return.

#### Request body

A CSV file (`"file"`) which contains the CSV file described above.

#### Response

JSON data in the following form

```json
{
    "updated_records": 123456
}
```

### GET `/v1/prices/search`

Search the cached TCG Player database for pricing and product data.

#### Request parameters

**Note**: Either `query`, `upc`, or `tcg_id` must be provided.

- `query` (`str`, optional): A query string to search for text contained in the product's set name, canonical TCG Player name, or card number.
- `tcg_id` (`str`, optional): The product's TCG Player ID
- `upc` (`str`, optional): The product's UPC (only searches sealed products)
- `type` (`str`): Either `card` or `sealed`.

#### Response

A JSON array of one or more items from the pricing database.

Sealed items are presented thusly:

```json
{
    "item_name": "Journey Together Elite Trainer Box",
    "sealed_low_price": 7498,
    "sealed_market_price": 7319,
    "set_name": "SV09: Journey Together",
    "tcg_id": 8492745,
    "upc": "196214108554"
}
```

Singles are presented thusly:

```json
{
    "attribute": "Holofoil",
    "card_name": "Umbreon VMAX (Alternate Art Secret)",
    "card_number": "215/203",
    "dm_market_price": 79000,
    "hp_market_price": 0,
    "lp_market_price": 137286,
    "mp_market_price": 114493,
    "nm_market_price": 144930,
    "set_name": "SWSH07: Evolving Skies",
    "tcg_id": 5150168
}
```

When there is not sufficient data to give a market price, its price will be `0`.

### PUT `/v1/prices/associateupc`

Associate a UPC with a sealed product. Does nothing if the product already has a UPC associated with it

#### Request parameters

- `tcg_id` (`str`): The TCG Player ID of the product
- `upc` (`str`): The product's UPC

### GET `/v1/users`

Get a list of all users.

Only admins can call this endpoint.

#### Response

A list of JSON data in the following format:

```json
{
    "created": "2025-05-30T16:22:45.652000Z",
    "last_logged_in": "2025-05-30T16:22:45.652000Z",
    "roles": "admin",
    "username": "test"
}
```

## POST `/v1/users/add`

Add or edit an existing user. If a user with the same username already exists, they will be replaced.

Only admins can call this endpoint.

#### Request body

A JSON object with the following data:

- `username` (`str`): The username of the user to add or edit
- `password` (`str`): The password of the user to add or edit
- `roles` (`str`): `"admin"` if this user is to be an admin, empty string otherwise


## DELETE `/v1/users/rm`

Delete a user.

Only admins can call this endpoint. 

#### Request parameters

- `username` (`str`): The username of the user to delete

## GET `/v1/settings/rates`

Fetch the buy rates currently stored.

Rates and cutoffs between tiers are structured in the form of arrays. For example, for the cutoffs `[2000, 5000, 10000]`, that means that anything below $20.00 (2,000 cents) is in tier 0, anything from $20.01 to $50.00 is tier 1, anything from $50.01 to $100.00 is tier 2, and anything above $100.00 is tier 3. The rates paid work similarly. For the rate array `[0.5, 0.6, 0.7, 0.8]`, that means 50% is paid on tier 0 items, 60% on tier 1 items, 70% on tier 2 items, and 80% on tier 3 items.

Note that the rate arrays must always be 1 longer than the cutoff arrays.

**Request parameters**

No parameters are required.

### Response

JSON data in the following format:

- `id` (`string`): Always `"rates"`
- `cutoffs` (`Object`): The cutoffs between different tiers for each of the product types
    - `card` (`Array<number>`): The monetary cutoffs between the tiers for singles
    - `slab` (`Array<number>`): The monetary cutoffs between the tiers for graded cards
    - `sealed` (`Array<number>`): The monetary cutoffs between the tiers for sealed product
- `cash_rates` (`Object`): The buy rates for when the customer wants to be paid in cash
    - `card` (`Array<number>`): The amount paid for each tier for singles
    - `slab` (`Array<number>`): The amount paid for each tier for graded cards
    - `sealed` (`Array<number>`): The amount paid for each tier for sealed product
- `credit_rates` (`Object`): The buy rates for when the customer wants store credit.
    - `card` (`Array<number>`): The amount paid for each tier for singles
    - `slab` (`Array<number>`): The amount paid for each tier for graded cards
    - `sealed` (`Array<number>`): The amount paid for each tier for sealed product