from pymongo import MongoClient
import json

with open('../settings.json', 'r') as f:
    settings = json.load(f)


db_client = MongoClient(settings['mongodb']['host'], settings['mongodb']['port'])
db = db_client['lgbt_scraper']
db_c = db['twitter']



while True:
    data = input("Data:")
    data = data.lower().strip()
    cat = input("green, red, related? [1/2/3]:")
    if cat == '1':
        cat = 'green'
    if cat == '2':
        cat = 'red'
    if cat == '3':
        cat = 'related'
    db_data = db_c.find_one({'data': data, 'type': 'word'})
    if db_data is not None:
        print('set already in DB!')
        continue
    d = {
        'type': 'word',
        'data': data,
        'category': cat
    }
    db_c.insert_one(d)
    print('done!')
