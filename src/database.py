import config
import pymongo

URI = f"mongodb+srv://{config.MONGODB_USERNAME}:{config.MONGODB_PASSWORD}@{config.MONGODB_CLUSTER}/?retryWrites=true&w=majority&appName={config.MONGODB_APPNAME}"

def get_db (org: str):
    """
    :param org: The organisation the user belongs to
    """
    return pymongo.MongoClient(URI, server_api=pymongo.server_api.ServerApi('1'))[org]
