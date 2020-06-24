import twitter
from datetime import datetime, timedelta
from email.utils import parsedate_tz

# fuck the twitter api srsly
def get_tweet_text(tweet):
    if tweet.retweeted_status is not None:
        return tweet.retweeted_status.full_text
    else:
        return tweet.full_text


def get_full_search_tweet_text(tweet):
    s = get_tweet_text(tweet)
    if tweet.quoted_status is not None:
        s += ' ' + tweet.quoted_status.full_text
    return s


# credit: https://stackoverflow.com/a/7704266/6376756
def to_datetime(datestring):
    time_tuple = parsedate_tz(datestring.strip())
    dt = datetime(*time_tuple[:6])
    return dt - timedelta(seconds=time_tuple[-1])


class TwitterHelper:
    def __init__(self, cfg):
        self.api = twitter.Api(
            cfg['consumer_key'],
            cfg['consumer_secret'],
            cfg['access_key'],
            cfg['access_secret'],
            tweet_mode='extended',
            sleep_on_rate_limit=True
        )
        self.get_tweets_retries = 5
        self.get_user_retries = 2

    def get_tweets(self, screen_name):
        timeline = None
        retry = 0
        while not timeline and retry < self.get_tweets_retries:
            retry += 1
            timeline = self.api.GetUserTimeline(screen_name=screen_name, count=200)
        if not timeline:
            return []
        earliest_tweet = min(timeline, key=lambda x: x.id).id
        while True:
            tweets = None
            retry = 0
            while not tweets and retry < self.get_tweets_retries:
                retry += 1
                tweets = self.api.GetUserTimeline(screen_name=screen_name, max_id=earliest_tweet, count=200)
            if not tweets:
                break
            new_earliest = min(tweets, key=lambda x: x.id).id
            if new_earliest == earliest_tweet:
                break
            earliest_tweet = new_earliest
            timeline += tweets
        return timeline

    def get_favorites(self, screen_name):
        retry = 0
        timeline = None
        while not timeline and retry < self.get_tweets_retries:
            retry += 1
            timeline = self.api.GetFavorites(screen_name=screen_name, count=200)
        if not timeline:
            return []
        earliest_tweet = min(timeline, key=lambda x: x.id).id
        while True:
            tweets = None
            retry = 0
            while not tweets and retry < self.get_tweets_retries:
                retry += 1
                tweets = self.api.GetFavorites(screen_name=screen_name, count=200, max_id=earliest_tweet)
            if not tweets:
                break
            new_earliest = min(timeline, key=lambda x: x.id).id
            if new_earliest == earliest_tweet:
                break
            earliest_tweet = new_earliest
            timeline += tweets
        return timeline

    def get_user_info(self, screen_name):
        data = None
        retry = 0
        while data is None and retry < self.get_user_retries:
            retry += 1
            try:
                data = self.api.GetUser(screen_name=screen_name)
            except:
                pass
        return data
