import pymongo

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
    

    if token is None or "Bearer " not in token:
        return ""
    
    tokens = CLIENT["route5"]["tokens"]
    token_record = tokens.find_one({"token": token[7:]})
    if token_record is None:
        return ""
    
    return token_record["name"]


