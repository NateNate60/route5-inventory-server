import config
import pymongo

URI = f"mongodb+srv://{config.MONGODB_USERNAME}:{config.MONGODB_PASSWORD}@{config.MONGODB_CLUSTER}/?retryWrites=true&w=majority&appName={config.MONGODB_APPNAME}"
DATABASE = pymongo.MongoClient(URI, server_api=pymongo.server_api.ServerApi('1'))['route5' if not config.TEST else 'route5test']
