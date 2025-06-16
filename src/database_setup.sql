USE route5prices;

CREATE TABLE IF NOT EXISTS pokemon (
    tcg_id CHAR(7) NOT NULL PRIMARY KEY,
    set_name VARCHAR(256) NOT NULL,
    card_name VARCHAR(256) NOT NULL,
    card_number VARCHAR(10) NOT NULL,
    condition CHAR(2) NOT NULL,
    tcg_market_price INTEGER NOT NULL,
    tcg_low_price INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS sealed (
    upc CHAR(12) NOT NULL PRIMARY KEY,
    item_name VARCHAR(256) NOT NULL,
    tcg_market_price INTEGER NOT NULL,
    tcg_low_price INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS users (
    username VARCHAR(31) NOT NULL PRIMARY KEY,
    password_hash CHAR(60) NOT NULL,
    roles VARCHAR(256)
)
