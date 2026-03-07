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
    attribute VARCHAR(255),
    photo_url VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS sealed (
    tcg_id INTEGER NOT NULL PRIMARY KEY,
    set_name VARCHAR(255) NOT NULL,
    item_name VARCHAR(255) NOT NULL,
    sealed_market_price INTEGER,
    sealed_low_price INTEGER,
    photo_url VARCHAR(255)
);

CREATE TABLE upc (
    tcg_id INTEGER NOT NULL,
    upc CHAR(13) NOT NULL,
    PRIMARY KEY (tcg_id, upc),
    FOREIGN KEY (tcg_id) REFERENCES sealed(tcg_id)
);

CREATE TABLE IF NOT EXISTS Users (
    org VARCHAR(32) NOT NULL,
    username VARCHAR(32) NOT NULL PRIMARY KEY,
    password_hash VARCHAR(64) NOT NULL,
    last_login DATETIME,
    created DATETIME,
    is_admin BOOLEAN
);

CREATE TABLE IF NOT EXISTS Inventory (
    item_id VARCHAR(16) NOT NULL,
    item_type VARCHAR(16) NOT NULL,
    description VARCHAR(255) NOT NULL,
    tcg_id INTEGER,
    acquired_date DATETIME NOT NULL,
    acquired_price DOUBLE NOT NULL,
    sale_price DOUBLE NOT NULL,
    item_condition VARCHAR(8) NOT NULL,
    quantity INTEGER NOT NULL,
    org VARCHAR(255) NOT NULL,
    PRIMARY KEY (item_id, org)
);

CREATE TABLE IF NOT EXISTS Sales (
    org VARCHAR(255) NOT NULL,
    username VARCHAR(255) NOT NULL,
    txid INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,
    sale_date DATETIME NOT NULL,
    sale_price_total DOUBLE NOT NULL,
    credit_applied DOUBLE NOT NULL,
    payment_method VARCHAR(16) NOT NULL,
    FOREIGN KEY (username) REFERENCES Users(username)
);

CREATE TABLE IF NOT EXISTS SellTxRow (
    txid INTEGER NOT NULL,
    item_id VARCHAR(16) NOT NULL,
    description VARCHAR(255) NOT NULL,
    sale_price DOUBLE NOT NULL,
    quantity INTEGER,
    acquired_price DOUBLE,
    tcg_id INTEGER,
    FOREIGN KEY (txid) REFERENCES Sales(txid),
    PRIMARY KEY (txid, item_id)
);

CREATE TABLE IF NOT EXISTS Buys (
    org VARCHAR(255) NOT NULL,
    username VARCHAR(255) NOT NULL,
    txid INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,
    acquired_date DATETIME NOT NULL,
    acquired_price_total DOUBLE NOT NULL,
    credit_given DOUBLE NOT NULL,
    payment_method VARCHAR(16) NOT NULL,
    FOREIGN KEY (username) REFERENCES Users(username)
);

CREATE TABLE IF NOT EXISTS BuyTxRow (
    txid INTEGER NOT NULL,
    item_id VARCHAR(16) NOT NULL,
    description VARCHAR(255) NOT NULL,
    acquired_price DOUBLE NOT NULL,
    market DOUBLE,
    quantity INTEGER NOT NULL,
    item_condition VARCHAR(8) NOT NULL,
    tcg_id INTEGER,
    FOREIGN KEY (txid) REFERENCES Buys(txid),
    PRIMARY KEY (txid, item_id)
);

CREATE TABLE IF NOT EXISTS Settings (
    org VARCHAR(255) NOT NULL PRIMARY KEY,
    threshold INTEGER NOT NULL,
    rates JSON
);