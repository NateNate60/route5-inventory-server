from dataclasses import dataclass, asdict

from database import MYSQL

@dataclass
class Card:
    tcg_id: str
    set_name: str
    card_name: str
    card_number: str
    nm_market_price: int
    lp_market_price: int
    mp_market_price: int
    hp_market_price: int
    dm_market_price: int
    attribute: str

    def to_dict (self):
        """
        Return a Card object as a dictionary.

        @return dict[str, str|int]: This Card object as a dictionary.
        """
        return asdict(self)

@dataclass
class Sealed:
    tcg_id: str
    set_name: str
    upc: str
    item_name: str
    sealed_market_price: int
    sealed_low_price: int

    def to_dict (self):
        """
        Return a Sealed object as a dictionary.

        @return dict[str, str|int]: This Sealed object as a dictionary.
        """
        return asdict(self)

def search_card_database (query: str) -> list[Card]:
    """
    Search the database by card name, returning a list of cards whose name, 
    set name, card number, or attribute contain one or more of the words in
    the query

    @param query (str): The query string
    @return list[Card]: A list of Card objects
    """
    name_words = query.split(' ')
    cursor = MYSQL.cursor()
    sql = ""
    vars: list[str] = []
    for word in name_words:
        sql += "AND CONCAT(set_name, ' ', card_name, ' ', card_number, ' ', attribute) LIKE CONCAT('%', %s ,'%') "
        vars.append(word)
    sql = "SELECT * FROM pokemon WHERE 1 " + sql + " LIMIT 20"
    cursor.execute(sql, vars)
    db_result = cursor.fetchall()
    MYSQL.commit()
    r: list[Card] = []
    for result in db_result:
        card = Card(
            tcg_id=result[0],
            set_name=result[1],
            card_name=result[2],
            card_number=result[3],
            nm_market_price=result[4],
            lp_market_price=result[5],
            mp_market_price=result[6],
            hp_market_price=result[7],
            dm_market_price=result[8],
            attribute=result[0]
        )
        r.append(card)
    return r

def card_database_by_id (tcg_id: str) -> Card | Sealed | None:
    """
    Query the card database by id

    @param tcg_id (str): The TCG Player ID or UPC of the card (use the ID for the NM version only) or sealed product
    @return Card|Sealed|None: A Card or Sealed object if the item was found, otherwise None
    """
    cursor = MYSQL.cursor()
    cursor.execute("SELECT * FROM pokemon WHERE tcg_id = %s", (tcg_id,))
    db_result = cursor.fetchall()
    if cursor.rowcount == 0:
        # Not in the pokemon table, try sealed
        cursor.execute("SELECT * FROM sealed WHERE tcg_id = %s OR (upc = %s AND upc != '')", (tcg_id, tcg_id))
        db_result = cursor.fetchall()
        MYSQL.commit()
        if cursor.rowcount == 0:
            # Not in the sealed table either
            return None
        for result in db_result:
            item = Sealed(
                tcg_id=result[0],
                set_name=result[1],
                upc=result[2],
                item_name=result[3],
                sealed_market_price=result[4],
                sealed_low_price=result[5]
            )
            return item

    item: Card = None
    for result in db_result:
        card = Card(
            tcg_id=result[0],
            set_name=result[1],
            card_name=result[2],
            card_number=result[3],
            nm_market_price=result[4],
            lp_market_price=result[5],
            mp_market_price=result[6],
            hp_market_price=result[7],
            dm_market_price=result[8],
            attribute=result[0]
        )
        item = card
        break
    return item

def search_sealed_database (query: str, upc_search: bool = False) -> list[Sealed]:
    """
    Search the database by product name, returning a list of products whose
    product name contains the query

    @param query (str): The query string
    @param upc_search (bool): Whether to search by UPC only
    @return list[Card]: A list of Card objects
    """
    cursor = MYSQL.cursor()
    if upc_search:
        cursor.execute("SELECT * FROM sealed WHERE upc = %s", (query,))
    else:
        cursor.execute("SELECT * FROM sealed WHERE item_name LIKE CONCAT('%', %s ,'%') LIMIT 10",
                    (query,))
    db_result = cursor.fetchall()
    MYSQL.commit()
    items: list[Sealed] = []
    for result in db_result:
        items.append(Sealed(
            tcg_id=result[0],
            set_name=result[1],
            upc=result[2],
            item_name=result[3],
            sealed_market_price=result[4],
            sealed_low_price=result[5]
        ))
    return items

def associate_upc (tcg_id: str, upc: str) -> int:
    """
    Affix a UPC to a given tcg_id

    @param tcg_id (str): The TCG Player ID of the item
    @param upc (str): The 12-digit UPC of the item
    @return int: The number of records updated (should be 0 or 1)
    """
    if len(upc) != 12:
        return 0
    cursor = MYSQL.cursor()
    cursor.execute("UPDATE sealed SET upc = %s WHERE tcg_id = %s AND upc = ''", 
                   (upc, tcg_id))
    MYSQL.commit()

    return cursor.rowcount