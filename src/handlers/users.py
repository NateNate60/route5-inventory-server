import flask
from datetime import datetime, timezone
from passlib.hash import bcrypt
from flask_jwt_extended import get_jwt, jwt_required
from authentication import admin_required
from database import get_db

users = flask.Blueprint('users', __name__)

@users.route("/v1/users", methods=["GET"])
@jwt_required()
def get_users ():
    claims = get_jwt()
    MYSQL = get_db()
    cursor = MYSQL.cursor()
    cursor.execute("SELECT * FROM Users WHERE org = %s", (claims['org'],))
    results = cursor.fetchall()
    users = [{
        "username": user[1],
        "last_login": user[3].timestamp(),
        "created": user[4].timestamp(),
        "is_admin": bool(user[5])
    } for user in results]
    
    cursor.close()
    return flask.jsonify(users)

@users.route("/v1/users", methods=["PATCH"])
@jwt_required()
def modify_user ():
    claims = get_jwt()
    
    data = flask.request.get_json()
    username = data.get('username')
    password = data.get('password')

    if type("username") is not str or type("password") is not str:
        return flask.Response('{"error": "Username or password not provided"}', status=400)

    admin = bool(data.get('admin'))

    if not claims['is_admin'] and claims['username'] != username:
        return flask.Response('{"error": "Unless you are an admin, you can only change your own password"}', status=403)

    DATABASE = get_db() 
    cursor = DATABASE.cursor()

    cursor.execute("UPDATE Users SET password_hash = %s WHERE username = %s AND org = %s", (bcrypt.hash(password), username, claims['org']))
    if (cursor.rowcount == 0):
        cursor.close()
        return flask.Response('{"error": "That user is not a member of your org"}', status=403)
    DATABASE.commit()
    cursor.close()

    return flask.Response("{}", status=200)
@users.route("/v1/users/add", methods=["POST"])
@jwt_required()
@admin_required()
def add_user ():
    claims = get_jwt()
    
    data = flask.request.get_json()
    username = data.get('username')
    password = data.get('password')

    if type("username") is not str or type("password") is not str:
        return flask.Response('{"error": "Username or password not provided"}', status=400)

    admin = bool(data.get('admin'))

    DATABASE = get_db() 
    cursor = DATABASE.cursor()

    cursor.execute("SELECT COUNT(*) FROM Users WHERE username = %s", (username,))
    if (cursor.fetchone()[0] != 0):
        cursor.close()
        return flask.Response('{"error": "Someone else is already using that username"}', status=409)
    
    cursor.execute("INSERT INTO Users VALUES (%s, %s, %s, NOW(), NOW(), %s)", (
        claims['org'],
        username,
        bcrypt.hash(password),
        admin
    ))
    DATABASE.commit()

    return flask.Response("{}", status=201)

@users.route("/v1/users/rm", methods=["DELETE"])
@jwt_required()
@admin_required()
def rm_user ():
    claims = get_jwt()

    username = flask.request.args.get("username")

    if type(username) is not str:
        return flask.Response('{"error": "Username not provided"}', status=400)
    DATABASE = get_db()
    cursor = DATABASE.cursor()

    cursor.execute("DELETE FROM Users WHERE org = %s AND username = %s", (claims['org'], username))
    if (cursor.rowcount == 0):
        DATABASE.commit()
        cursor.close()
        return flask.Response('{"error": "Username not found"}', status=404)
    DATABASE.commit()
    cursor.close()
    return flask.Response("{}", status=200)