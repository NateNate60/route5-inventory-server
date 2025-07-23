USE route5prices;

CREATE TABLE IF NOT EXISTS pokemon (
    tcg_id INTEGER NOT NULL PRIMARY KEY,
    set_name VARCHAR(255) NOT NULL,
    card_name VARCHAR(255) NOT NULL,
    card_number VARCHAR(31) NOT NULL,
    nm_market_price INTEGER,
    lp_market_price INTEGER,
    mp_market_price INTEGER,
    hp_market_price INTEGER,
    dm_market_price INTEGER,
    nm_low_price INTEGER,
    lp_low_price INTEGER,
    mp_low_price INTEGER,
    hp_low_price INTEGER,
    dm_low_price INTEGER,
    attribute VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS sealed (
    tcg_id INTEGER NOT NULL PRIMARY KEY,
    set_name VARCHAR(255) NOT NULL,
    upc CHAR(12),
    item_name VARCHAR(255) NOT NULL,
    sealed_market_price INTEGER,
    sealed_low_price INTEGER
);