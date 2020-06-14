from aiohttp import web
import aiohttp_jinja2
import praw
import jinja2
from os import path
from prawcore.exceptions import NotFound
from dateutil.relativedelta import relativedelta
import json
from aiohttp.abc import AbstractAccessLogger
import logging
from datetime import datetime
from pymongo import MongoClient
import asyncio
import concurrent.futures
import re
import twitter_helper as th
from twitter.error import TwitterError


class AccessLogger(AbstractAccessLogger):

    def log(self, request, response, time):
        self.logger.info(f'[{datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")}] '
                         f'{request.remote} '
                         f'"{request.method} {request.rel_url}" '
                         f'done in {time}s: {response.status} '
                         f'- "{request.headers.get("User-Agent")}"')


# ======================================================================================================================
# Init
# ======================================================================================================================


with open('settings.json', 'r') as f:
    settings = json.load(f)

rs = settings['reddit']
reddit = praw.Reddit(client_secret=rs['client_secret'], client_id=rs['client_id'],
                     username=rs['username'], password=rs['password'],
                     user_agent=rs['user_agent'])

twitter = th.TwitterHelper(settings['twitter'])

db_client = MongoClient(settings['mongodb']['host'], settings['mongodb']['port'])
db = db_client[settings['mongodb']['db']]
db_reddit = db['reddit']
db_twitter = db['twitter']

REMOVED_CHARS = re.compile(r'[.,:;!?+(){}<>\*\[\]]')
TWITTER_PROFILE_URL_FIX = re.compile(r'_normal')

executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)

# ======================================================================================================================
# Helpers
# ======================================================================================================================


def get_data(use_db):
    data = {}
    for cat in ['red', 'green', 'related']:
        data[cat] = {
            'subs': [k.get('data') for k in use_db.find({'category': cat, 'type': 'subreddit'})],
            'words': [k.get('data') for k in use_db.find({'category': cat, 'type': 'word'})]
        }
    return data


def get_date_since_str(date_str):
    if isinstance(date_str, float):
        since = datetime.utcfromtimestamp(date_str)
    else:
        since = date_str
    delta = relativedelta(datetime.utcnow(), since)
    delta_str = ""
    if delta.days == 0 and delta.years == 0 and delta.months == 0 and \
            delta.hours == 0 and delta.minutes == 0 and delta.seconds == 0:
        delta_str = 'now'
    else:
        if delta.years > 0:
            delta_str += f"{delta.years} year"
            if delta.years > 1:
                delta_str += "s"
        if delta.months > 0:
            if len(delta_str) > 0:
                delta_str += ", "
            delta_str += f"{delta.months} month"
            if delta.months > 1:
                delta_str += "s"
        if delta.days > 0:
            if len(delta_str) > 0:
                delta_str += ", "
            delta_str += f"{delta.days} day"
            if delta.days > 1:
                delta_str += "s"
        if len(delta_str) == 0:
            if delta.hours > 0:
                if len(delta_str) > 0:
                    delta_str += ", "
                delta_str += f"{delta.hours} hour"
                if delta.hours > 1:
                    delta_str += "s"
            else:
                if delta.minutes > 0:
                    if len(delta_str) > 0:
                        delta_str += ", "
                    delta_str += f"{delta.minutes} minute"
                    if delta.minutes > 1:
                        delta_str += "s"
                if delta.seconds > 0:
                    if len(delta_str) > 0:
                        delta_str += ", "
                    delta_str += f"{delta.seconds} second"
                    if delta.seconds > 1:
                        delta_str += "s"
    return delta_str

# ======================================================================================================================
# API Queries
# ======================================================================================================================


def query_reddit(user):
    start_time = datetime.utcnow()
    data = {}
    if user is not None:
        user = user.strip()
        u = reddit.redditor(user)
        try:
            u.id
        except NotFound:
            return {'error': {
                'reason': 'User not found!'
            }}
        cat_data = get_data(db_reddit)
        c_ = {
            'red': [],
            'green': [],
            'related': []
        }
        c_t = 0
        p_t = 0
        for comment in u.comments.new(limit=None):
            c_t += 1
            subname = comment.subreddit_name_prefixed[2:].lower()
            url = f'https://reddit.com{comment.permalink}?context=8&depth=9'
            c_data = {
                    'body': comment.body.replace('&#x200B;', ''),
                    'sub': comment.subreddit_name_prefixed[2:],
                    'score': comment.score,
                    'url': url,
                    'title': comment.link_title,
                    'type': 'comment',
                    'date': comment.created_utc,
                    'days_since': get_date_since_str(comment.created_utc)
                }
            prep_body = REMOVED_CHARS.sub(' ', comment.body.lower()).split()
            for key, item in cat_data.items():
                if subname in item['subs'] or any(word in prep_body for word in item['words']):
                    c_[key].append(c_data)
                    break

        for post in u.submissions.new(limit=None):
            p_t += 1
            subname = post.subreddit_name_prefixed[2:].lower()
            url = post.shortlink
            p_data = {
                'body': post.selftext,
                'sub': post.subreddit_name_prefixed[2:],
                'score': post.score,
                'url': url,
                'title': post.title,
                'type': 'post',
                'date': post.created_utc,
                'days_since': get_date_since_str(post.created_utc)
            }
            prep_search = REMOVED_CHARS.sub(' ', f'{post.selftext} {post.title}'.lower()).split()
            for key, item in cat_data.items():
                if subname in item['subs'] or any(word in prep_search for word in item['words']):
                    c_[key].append(p_data)
                    break

        for key, item in c_.items():
            c_[key] = sorted(item, key=lambda d: d['date'], reverse=True)
        usr = {
            'name': u.name,
            'account_age': get_date_since_str(u.created_utc),
            'profile_pic': u.icon_img,
            'comment_karma': u.comment_karma,
            'link_karma': u.link_karma,
            'good': c_['green'],
            'flag': c_['red'],
            'related': c_['related'],
            'description': u.subreddit.get('public_description')
        }
        data['user'] = usr
        data['processing_time'] = get_date_since_str(start_time)
        data['comment_count'] = c_t
        data['post_count'] = p_t
    return data


def twitter_data(user):
    def build_tweet_data(tweet, tweet_type):
        data = {
            'text': th.get_tweet_text(tweet),
            'full_text': th.get_full_search_tweet_text(tweet),
            'id': tweet.id_str,
            'old_id': tweet.id,
            'type': tweet_type,
            'url': f'https://twitter.com/{user}/status/{tweet.id_str}',
            'age': get_date_since_str(th.to_datetime(tweet.created_at))
            }
        if tweet.quoted_status is not None:
            t = tweet.quoted_status
            qt = {
                'text': t.full_text,
                'id': t.id_str,
                'old_id': t.id,
                'type': 'tweet',
                'user_name': t.user.screen_name,
                'age': get_date_since_str(th.to_datetime(t.created_at)),
                'url': f'https://twitter.com/{t.user.screen_name}/status/{t.id_str}'
            }
            data['quoted'] = qt
        if tweet.retweeted_status is not None:
            t = tweet.retweeted_status
            rt = {
                'user_name': t.user.screen_name
            }
            data['retweeted'] = rt
        return data

    tweets = twitter.get_tweets(user)
    likes = twitter.get_favorites(user)
    data = [build_tweet_data(t, 'tweet') for t in tweets]
    data.extend([build_tweet_data(t, 'like') for t in likes])
    return sorted(data, key=lambda d: d['id'], reverse=True), len(tweets), len(likes)


def query_twitter(user):
    start_time = datetime.utcnow()
    data = {}
    if user is not None:
        try:
            usr_d = twitter.get_user_info(user)
        except TwitterError:
            return {
                'error': {
                    'reason': 'User not found'
                }
            }
        tweets, c_t, c_l = twitter_data(user)
        cat_data = get_data(db_twitter)
        c_ = {
            'red': [],
            'green': [],
            'related': []
        }
        for tweet in tweets:
            body = REMOVED_CHARS.sub(' ', tweet["full_text"].lower()).split()
            for key, item in cat_data.items():
                if any(word in body for word in item['words']):
                    c_[key].append(tweet)
        usr = {
            'name': usr_d.screen_name,
            'good': c_['green'],
            'flag': c_['red'],
            'related': c_['related'],
            'account_age': get_date_since_str(th.to_datetime(usr_d.created_at)),
            'description': usr_d.description,
            'display_name': usr_d.name,
            'followers_count': usr_d.followers_count,
            'friends_count': usr_d.friends_count,
            'tweets_count': usr_d.statuses_count if c_t < usr_d.statuses_count else c_t,
            'favourites_count': usr_d.favourites_count if c_l < usr_d.favourites_count else c_l,
            'verified': usr_d.verified,
            'profile_pic': TWITTER_PROFILE_URL_FIX.sub('', usr_d.profile_image_url_https)
        }
        data['user'] = usr
        data['count_tweets'] = c_t
        data['count_likes'] = c_l
        data['processing_time'] = get_date_since_str(start_time)
    return data


# ======================================================================================================================
# Request Handlers
# ======================================================================================================================


@aiohttp_jinja2.template('list_reddit.html.j2')
async def handle_load_list_reddit(request):
    user = request.match_info['user_name']
    try:
        completed, pending = await asyncio.wait([asyncio.get_event_loop().run_in_executor(executor, query_reddit, user)])
        results = [t.result() for t in completed]
        return results[0]
    except:
        return {
            'error': {
                'reason': 'An error occurred while trying to scrape the account. Please try again in a bit.'
            }
        }


@aiohttp_jinja2.template('list_twitter.html.j2')
async def handle_load_list_twitter(request):
    try:
        user = request.match_info['user_name']
        completed, pending = await asyncio.wait([asyncio.get_event_loop().run_in_executor(executor, query_twitter, user)])
        results = [t.result() for t in completed]
        return results[0]
    except:
        return {
            'error': {
                'reason': 'An error occurred while trying to scrape the account. It might be set to private.'
            }
        }


@aiohttp_jinja2.template('config.html.j2')
async def handle_show_settings(request):
    return {
        "lgbt_subs": [],
        "flag_subs": []
    }


@aiohttp_jinja2.template('reddit.html.j2')
async def handle_reddit(request):
    user_name = request.match_info['user_name']
    data = {}
    if user_name is not None and len(user_name) > 0:
        username = user_name.strip()
        usr = {
            'name': username,
        }
        data['user'] = usr
    return data


@aiohttp_jinja2.template('twitter.html.j2')
async def handle_twitter(request):
    user_name = request.match_info['user_name']
    data = {}
    if user_name is not None and len(user_name) > 0:
        username = user_name.strip()
        usr = {
            'name': username,
        }
        data['user'] = usr
    return data


@aiohttp_jinja2.template('home.html.j2')
async def handle_home(request):
    data = {
        'factor_count': {
            'reddit': db_reddit.count_documents({}),
            'twitter': db_twitter.count_documents({})
        }
    }
    return data

# ======================================================================================================================
# Service Startup
# ======================================================================================================================


app = web.Application()
aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader('templates'))
app.add_routes([web.get('/', handle_home),
                web.get('/t/{user_name}', handle_twitter),
                web.get('/twitter/{user_name}', handle_twitter),
                web.get('/r/{user_name}', handle_reddit),
                web.get('/reddit/{user_name}', handle_reddit),
                web.get('/ajax/reddit/{user_name}', handle_load_list_reddit),
                web.get('/ajax/twitter/{user_name}', handle_load_list_twitter)])
app.router.add_static('/static/',
                      path=str(path.join(path.dirname(__file__), 'static/')),
                      name='static')
app.logger.setLevel(logging.INFO)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, handlers=[logging.FileHandler('access.log')])
    web.run_app(app, port=settings['port'], access_log_class=AccessLogger)
