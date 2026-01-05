from mysql import connector
from src import config
import csv
import datetime

def process (filename: str) -> None:
    with open(filename, "r") as f:
        MYSQL = connector.connect(host="localhost", user=config.MYSQL_USER, password=config.MYSQL_PASSWORD, database="route5prices", connection_timeout=3600)
        cursor = MYSQL.cursor()
        reader = csv.reader(f)
        count = 0
        start_time = datetime.datetime.now().timestamp()
        for row in reader:
            # Empty string means no data, replace with 0
            if row[8] == "":
                row[8] = "0"
            if row[11] == "":
                row[11] = "0"

            if "TCGplayer Id" in row:
                # This is the first row and contains column headers
                continue
            elif "Unopened" == row[7]:
                cursor.execute("INSERT INTO sealed VALUES (%s, %s, %s, %s, %s, %s, '') ON DUPLICATE KEY UPDATE " \
                                "sealed_market_price = %s," \
                                "sealed_low_price = %s", (
                                row[0],
                                row[2],
                                "",
                                row[3],
                                int(float(row[8]) * 100),
                                int(float(row[11]) * 100),
                                int(float(row[8]) * 100),
                                int(float(row[11]) * 100),
                                ))
                MYSQL.commit()
            elif "Near Mint" in row[7]:
                attribute = "".join(row[7].split(" ")[2:])
                lp_row = next(reader, None)
                mp_row = next(reader, None)
                hp_row = next(reader, None)
                dm_row = next(reader, None)
                if lp_row[8] == "":
                    lp_row[8] = 0
                if mp_row[8] == "":
                    mp_row[8] = 0
                if hp_row[8] == "":
                    hp_row[8] = 0
                if dm_row[8] == "":
                    dm_row[8] = 0
                if lp_row[11] == "":
                    lp_row[11] = 0
                if mp_row[11] == "":
                    mp_row[11] = 0
                if hp_row[11] == "":
                    hp_row[11] = 0
                if dm_row[11] == "":
                    dm_row[11] = 0
                cursor.execute("INSERT INTO pokemon VALUES (%(tcgid)s, %(setname)s, %(cardname)s, %(cardnumber)s, " \
                                "%(nm)s, %(lp)s, %(mp)s, %(hp)s, %(dm)s, %(nml)s, " \
                                "%(lpl)s, %(mpl)s, %(hpl)s, %(dml)s, %(attribute)s, '') " \
                                "ON DUPLICATE KEY UPDATE " \
                                "nm_market_price = %(nm)s, " \
                                "lp_market_price = %(lp)s, " \
                                "mp_market_price = %(mp)s, " \
                                "hp_market_price = %(hp)s, " \
                                "dm_market_price = %(dm)s, "  \
                                "nm_low_price = %(nml)s, " \
                                "lp_low_price = %(lpl)s, " \
                                "mp_low_price = %(mpl)s, " \
                                "hp_low_price = %(hpl)s, " \
                                "dm_low_price = %(dml)s, " \
                                "photo_url = '' " \
                                    , {
                                    "tcgid": row[0],
                                    # Column 1 always says "pokemon"
                                    "setname": row[2],
                                    "cardname": row[3],
                                    # Column 4 is blank
                                    "cardnumber": row[5],
                                    "nm": int(float(row[8]) * 100),
                                    "lp": int(float(lp_row[8]) * 100),
                                    "mp": int(float(mp_row[8]) * 100),
                                    "hp": int(float(hp_row[8]) * 100),
                                    "dm": int(float(dm_row[8]) * 100),
                                    "nml": int(float(row[11]) * 100),
                                    "lpl": int(float(lp_row[11]) * 100),
                                    "mpl": int(float(mp_row[11]) * 100),
                                    "hpl": int(float(hp_row[11]) * 100),
                                    "dml": int(float(dm_row[11]) * 100), 
                                    "attribute": attribute,
                                })
                MYSQL.commit()
                count += 4
                
            elif "Damaged" in row[7]:
                cursor.execute("UPDATE pokemon SET dm_market_price = %s WHERE tcg_id = %s",
                               (int(float(row[8]) * 100), int(row[0]) - 4))
                MYSQL.commit()
            elif "Heavily Played" in row[7]:
                cursor.execute("UPDATE pokemon SET hp_market_price = %s WHERE tcg_id = %s",
                               (int(float(row[8]) * 100), int(row[0]) - 3))
                MYSQL.commit()
            elif "Moderately Played" in row[7]:
                cursor.execute("UPDATE pokemon SET mp_market_price = %s WHERE tcg_id = %s",
                               (int(float(row[8]) * 100), int(row[0]) - 2))
                MYSQL.commit()
            elif "Lightly Played" in row[7]:
                cursor.execute("UPDATE pokemon SET lp_market_price = %s WHERE tcg_id = %s",
                               (int(float(row[8]) * 100), int(row[0]) - 1))
                MYSQL.commit()
            else:
                continue
            count += 1
            if count % 500 == 0:
                print(count, end='\r')

    end_time = datetime.datetime.now().timestamp()
    print(f"Updated {count} records in {int(end_time - start_time)} seconds, avg {int(count / (end_time - start_time))} records/s")


def main ():
    print("Processing EN")
    process("en.csv")
    print("Processing JP")
    process("jp.csv")
    print("Processing MTG")
    process("mtg.csv")

if __name__ == "__main__":
    main()