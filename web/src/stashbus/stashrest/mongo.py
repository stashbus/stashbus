# mongorest/mongo.py
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

client: MongoClient = MongoClient("mongodb://root:example@mongo:27017/")
db: Database = client["stashbus"]
btc_prices: Collection = db["stashbus/prices/btc_usd"]
brno_weather: Collection = db["stashbus/weather/brno"]
