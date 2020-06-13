from pymongo import MongoClient
import json

with open('../settings.json', 'r') as f:
    settings = json.load(f)


db_client = MongoClient(settings['mongodb']['host'], settings['mongodb']['port'])
db = db_client['lgbt_scraper']
db_c = db['reddit']
db_t = db['twitter']


data = db_c.find({'type': 'word'})

for dat in data:
    db_t.insert_one(dat)
