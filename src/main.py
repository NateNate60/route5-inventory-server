import flask
import pymongo
from datetime import datetime, timedelta

import config
from authentication import authenticate
from database import DATABASE

from handlers.inventory import inventory
from handlers.transactions import transactions

app = flask.Flask(__name__)

app.register_blueprint(inventory)
app.register_blueprint(transactions)