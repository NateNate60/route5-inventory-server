import config
import pymongo
from mysql import connector

URI = f"mongodb+srv://{config.MONGODB_USERNAME}:{config.MONGODB_PASSWORD}@{config.MONGODB_CLUSTER}/?retryWrites=true&w=majority&appName={config.MONGODB_APPNAME}"
DATABASE = pymongo.MongoClient(URI, server_api=pymongo.server_api.ServerApi('1'))['route5' if not config.TEST else 'route5test']
MYSQL = connector.connect(host="localhost", user=config.MYSQL_USER, password=config.MYSQL_PASSWORD, database="route5prices", connection_timeout=864000)