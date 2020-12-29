from pymongo import MongoClient
import json
import csv


with open('../settings.json', 'r') as f:
    settings = json.load(f)


db_client = MongoClient(settings['mongodb']['host'], settings['mongodb']['port'])
db = db_client['lgbt_scraper']
db_c = db['reddit']


subreddits = []
keywords = []

data = db_c.find({})

with open('dump_subs.csv', 'w', newline='') as subs_file:
    with open('dump_keywords.csv', 'w', newline='') as key_file:
        subs_writer = csv.writer(subs_file, delimiter=';', quoting=csv.QUOTE_MINIMAL)
        key_writer = csv.writer(key_file, delimiter=';', quoting=csv.QUOTE_MINIMAL)
        for d in data:
            if d.get('type') == 'subreddit':
                subs_writer.writerow([d.get('category'), d.get('data')])
            else:
                key_writer.writerow([d.get('category'), d.get('data')])
