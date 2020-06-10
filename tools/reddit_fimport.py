from pymongo import MongoClient
import json

with open('../settings.json', 'r') as f:
    settings = json.load(f)

with open('../data/related_words.json', 'r') as f:
    lgbt_subs = json.load(f)

db_client = MongoClient(settings['mongodb']['host'], settings['mongodb']['port'])
db = db_client['lgbt_scraper']
db_c = db['reddit']

for sub in lgbt_subs:
    t = 's'
    data = sub
    data = data.lower().strip()
    cat = '1' # input("green, red, related? [1/2/3]:")
    db_data = db_c.find_one({'data': data})
    if db_data is not None:
        print('set already in DB!')
        continue
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
    d = {
        'type': t,
        'data': data,
        'category': cat
    }
    db_c.insert_one(d)
    print(f'added {sub}!')
