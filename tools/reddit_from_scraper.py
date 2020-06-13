from pymongo import MongoClient, DESCENDING
import json

with open('../settings.json', 'r') as f:
    settings = json.load(f)


db_client = MongoClient(settings['mongodb']['host'], settings['mongodb']['port'])
db = db_client['lgbt_scraper']
db_c = db['reddit']

db_ss = db_client['subreddit_prober']
db_s = db_ss['subreddit']

potential_data = db_s.find({'sub': {'$regex': '.*wlw.*'}}).sort([("nr_of_users", DESCENDING)])

for pot_dat in potential_data:
    t = 'subreddit' # input("Subreddit or Word [s/w]:")
    data = pot_dat.get('sub').lower().strip()
    db_data = db_c.find_one({'data': data, 'type': t})
    if db_data is not None:
        continue
    desc = pot_dat.get("description", "no description")
    desc = desc.replace('\r', '').replace('\n\n', '\n')
    d2 = pot_dat.get("public_description", "no public description")
    d2 = d2.replace('\r', '').replace('\n\n', '\n')
    nr = pot_dat.get('nr_of_users', 0)
    print(f'\n\n\n================================================='
          f'================================================='
          f'================================================='
          f'\nSub: {data} (https://reddit.com/r/{data}/)\nUsers: {nr}\n{desc}\n{d2}')

    cat = input("green, red, related, unrelated? [1/2/3/4]:")
    if cat == '1':
        cat = 'green'
    if cat == '2':
        cat = 'red'
    if cat == '3':
        cat = 'related'
    if cat == '4':
        cat = 'unrelated'
    d = {
        'type': t,
        'data': data,
        'category': cat
    }
    db_c.insert_one(d)
    print('done!')
