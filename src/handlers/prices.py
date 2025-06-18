import flask
import csv
import datetime
from flask_jwt_extended import jwt_required
from werkzeug.utils import secure_filename
from database import MYSQL
from mysql.connector.errors import IntegrityError

from tcgplayer import search_card_database_by_name

prices = flask.Blueprint('prices', __name__)

@prices.route("/v1/prices/update", methods=["POST"])
# @jwt_required()
def process_update ():

    t = search_card_database_by_name("Umbreon VMAX 215")

    if "file" not in flask.request.files:
        return flask.Response('{"error": "No file uploaded"}', status=400)
    file = flask.request.files["file"]
    if file.filename == "" or file.filename is None:
        return flask.Response('{"error": "No file uploaded"}', status=400)
    if file.filename.lower().split('.')[-1] != "csv":
        return flask.Response('{"error": "File uploaded is not a CSV"}', status=422)
    filename = f"/tmp/{secure_filename(file.filename)}"
    file.save(filename)

    with open(filename, "r") as f:
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
                cursor.execute("INSERT INTO sealed VALUES (%s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE " \
                                "sealed_market_price = %s," \
                                "sealed_low_price = %s", (
                                row[0],
                                "000000000000",
                                row[3],
                                int(float(row[8]) * 100),
                                int(float(row[11]) * 100),
                                int(float(row[8]) * 100),
                                int(float(row[11]) * 100)
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
                cursor.execute("INSERT INTO pokemon VALUES (%(tcgid)s, %(setname)s, %(cardname)s, %(cardnumber)s, "
                                "%(nm)s, %(lp)s, %(mp)s, %(hp)s, %(dm)s, %(attribute)s) " \
                                "ON DUPLICATE KEY UPDATE " \
                                "nm_market_price = %(nm)s, " \
                                "lp_market_price = %(lp)s, " \
                                "mp_market_price = %(mp)s, " \
                                "hp_market_price = %(hp)s, " \
                                "dm_market_price = %(dm)s " , {
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
    print(f"Updated {count} records in {end_time - start_time} seconds, avg {count / (end_time - start_time)} records/s")
    return flask.jsonify({
        "updated_records": count
    })
