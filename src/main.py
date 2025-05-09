import flask
import flask_cors
from datetime import datetime, timedelta

from authentication import authenticate
from database import DATABASE

from handlers.inventory import inventory
from handlers.transactions import transactions

app = flask.Flask(__name__)

app.register_blueprint(inventory)
app.register_blueprint(transactions)

flask_cors.CORS(app)