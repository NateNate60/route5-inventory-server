import flask
import flask_cors
import flask_jwt_extended
from config import TEST
from datetime import datetime, timedelta

from database import DATABASE

from handlers.inventory import inventory
from handlers.transactions import transactions
from handlers.psa import psa
from handlers.login import login
from handlers.users import users

app = flask.Flask(__name__)

app.register_blueprint(inventory)
app.register_blueprint(transactions)
app.register_blueprint(psa)
app.register_blueprint(login)
app.register_blueprint(users)

jwt = flask_jwt_extended.JWTManager(app)
app.config["JWT_COOKIE_SECURE"] = not TEST
app.config["JWT_TOKEN_LOCATION"] = ["headers"]
app.config["JWT_SECRET_KEY"] = "super-secret"  # Change this in your code!
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(minutes=20)
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=30)

flask_cors.CORS(app)