USE route5prices;

CREATE TABLE IF NOT EXISTS pokemon (
    tcg_id CHAR(7) NOT NULL PRIMARY KEY,
    set_name VARCHAR(255) NOT NULL,
    card_name VARCHAR(255) NOT NULL,
    card_number VARCHAR(31) NOT NULL,
    nm_market_price INTEGER,
    lp_market_price INTEGER,
    mp_market_price INTEGER,
    hp_market_price INTEGER,
    dm_market_price INTEGER,
    attribute VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS sealed (
    tcg_id CHAR(7) NOT NULL PRIMARY KEY,
    upc CHAR(12),
    item_name VARCHAR(255) NOT NULL,
    sealed_market_price INTEGER,
    sealed_low_price INTEGER
);