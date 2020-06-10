from pymongo import MongoClient
import json

with open('../settings.json', 'r') as f:
    settings = json.load(f)


db_client = MongoClient(settings['mongodb']['host'], settings['mongodb']['port'])
db = db_client['lgbt_scraper']
db_c = db['reddit']

while True:
    t = 's' # input("Subreddit or Word [s/w]:")
    data = input("Data:")
    data = data.lower().strip()
    cat = '3' # input("green, red, related? [1/2/3]:")
    if t == 's':
        t = 'subreddit'
    else:
        t = 'word'
    if cat == '1':
        cat = 'green'
    if cat == '2':
        cat = 'red'
    if cat == '3':
        cat = 'related'
    db_data = db_c.find_one({'data': data, 'type': t})
    if db_data is not None:
        print('set already in DB!')
        continue
    d = {
        'type': t,
        'data': data,
        'category': cat
    }
    db_c.insert_one(d)
    print('done!')
