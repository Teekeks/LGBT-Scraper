import json
import twitter

with open('../settings.json', 'r') as f:
    settings = json.load(f)

cfg = settings['twitter']

api = twitter.Api(
            cfg['consumer_key'],
            cfg['consumer_secret'],
            cfg['access_key'],
            cfg['access_secret'],
            tweet_mode='extended'
        )

data = api.GetStatus(status_id=1268361411266256897)
print(json.dumps(data._json))

