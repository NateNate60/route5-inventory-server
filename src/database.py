import config
from mysql import connector

URI = f"mongodb+srv://{config.MONGODB_USERNAME}:{config.MONGODB_PASSWORD}@{config.MONGODB_CLUSTER}/?retryWrites=true&w=majority&appName={config.MONGODB_APPNAME}"

def get_db ():
    """
    :param org: The organisation the user belongs to
    """
    return connector.connect(host="localhost", user=config.MYSQL_USER, password=config.MYSQL_PASSWORD, database="route5prices", connection_timeout=60)

