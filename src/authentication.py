import pymongo
import pymongo.server_api

import config

URI = f"mongodb+srv://{config.MONGODB_USERNAME}:{config.MONGODB_PASSWORD}@{config.MONGODB_CLUSTER}/?retryWrites=true&w=majority&appName={config.MONGODB_APPNAME}"

CLIENT = pymongo.MongoClient(URI, server_api=pymongo.server_api.ServerApi('1'))

def authenticate (token: str) -> str :
    """
    Check whether a given token is valid.

    Parameters
        token (str): The token to check.

    Return
        The name of the user if valid, empty string if not.
    """
    tokens = CLIENT["route5"]["Tokens"]

    token_record = tokens.find_one({"token": token})
    if token_record is None:
        return ""
    
    return token_record["name"]


