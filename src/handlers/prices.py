import flask
import csv
import datetime
from flask_jwt_extended import jwt_required
from werkzeug.utils import secure_filename
from database import MYSQL
from mysql.connector.errors import IntegrityError

prices = flask.Blueprint('prices', __name__)

@prices.route("/v1/prices/update", methods=["POST"])
@jwt_required()
def process_update ():
    if "file" not in flask.request.files:
        return flask.Response('{"error": "No file uploaded"}', status=400)
    file = flask.request.files["file"]
    if file.filename == "":
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
                cursor.execute("UPDATE sealed SET sealed_market_price = %s, sealed_low_price = %s WHERE tcg_id = %s",
                               (int(float(row[8]) * 100), int(float(row[11]) * 100), row[0]))
                MYSQL.commit()
                if (cursor.rowcount == 0):
                    try: 
                        cursor.execute("INSERT INTO sealed VALUES (%s, %s, %s, %s, %s)", (
                                        row[0],
                                        "000000000000",
                                        row[3],
                                        int(float(row[8]) * 100),
                                        int(float(row[11]) * 100)
                                        ))
                        MYSQL.commit()
                    except IntegrityError:
                        pass
            elif "Near Mint" in row[7]:
                cursor.execute("UPDATE pokemon SET nm_market_price = %s WHERE tcg_id = %s",
                               (int(float(row[8]) * 100), row[0]))
                MYSQL.commit()
                if (cursor.rowcount == 0):
                    attribute = "".join(row[7].split(" ")[2:])
                    try:
                        cursor.execute("INSERT INTO pokemon VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (
                                        row[0],
                                        # Column 1 always says "pokemon"
                                        row[2],
                                        row[3],
                                        # Column 4 is blank
                                        row[5],
                                        int(float(row[8]) * 100),
                                        0, 0, 0, 0, attribute
                                        ))
                        MYSQL.commit()
                    except IntegrityError:
                         pass
            elif "Damaged" in row[7]:
                cursor.execute("UPDATE pokemon SET dm_market_price = %s WHERE tcg_id = %s",
                               (row[8], row[0]))
                MYSQL.commit()
            elif "Heavily Played" in row[7]:
                cursor.execute("UPDATE pokemon SET hp_market_price = %s WHERE tcg_id = %s",
                               (row[8], row[0]))
                MYSQL.commit()
            elif "Moderately Played" in row[7]:
                cursor.execute("UPDATE pokemon SET mp_market_price = %s WHERE tcg_id = %s",
                               (row[8], row[0]))
                MYSQL.commit()
            elif "Lightly Played" in row[7]:
                cursor.execute("UPDATE pokemon SET lp_market_price = %s WHERE tcg_id = %s",
                               (row[8], row[0]))
                MYSQL.commit()
            else:
                continue
            count += 1

    end_time = datetime.datetime.now().timestamp()
    print(f"Updated {count} records in {end_time - start_time} seconds, avg {count / (end_time - start_time)} records/s")
    return flask.jsonify({
        "updated_records": count
    })