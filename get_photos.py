import requests
from mysql import connector
from src import config

def get_en_sets() -> list[str]:
    tcgcsv = requests.get("https://tcgcsv.com/tcgplayer/3/groups").json()
    en = tcgcsv.get("results")
    return [set_info["groupId"] for set_info in en]

def get_jp_sets() -> list[str]:
    tcgcsv = requests.get("https://tcgcsv.com/tcgplayer/85/groups").json()
    jp = tcgcsv.get("results")
    return [set_info["groupId"] for set_info in jp]

def process_set(setID, language) :
    MYSQL = connector.connect(host="localhost", user=config.MYSQL_USER, password=config.MYSQL_PASSWORD, database="route5prices", connection_timeout=30)
    cursor = MYSQL.cursor()

    tcgcsv = requests.get(f"https://tcgcsv.com/tcgplayer/{language}/{setID}/products").json()
    results = tcgcsv.get("results")
    for product in results:
        if len(product["extendedData"]) < 2:
            cursor.execute("UPDATE sealed SET photo_url = %s WHERE item_name = %s", (product["imageUrl"], product["name"]))
        else:
            if product["extendedData"][0]["name"] == "Number":
                number = product["extendedData"][0]["value"]
            else:
                number = product["extendedData"][1]["value"]
            cursor.execute("UPDATE pokemon SET photo_url = %s WHERE card_name = %s AND card_number = %s", (
                product["imageUrl"],
                product["name"],
                number
            ))
        MYSQL.commit()

def main():
    en_sets = get_en_sets()
    jp_sets = get_jp_sets()
    completed = 0
    for setID in en_sets:
        process_set(setID, 3)
        completed += 1
        print(f"Completed {completed} sets", end='\r')
    for setID in jp_sets:
        process_set(setID, 85)
        completed += 1
        print(f"Completed {completed} sets", end='\r')

if __name__ == "__main__":
    main()