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
# import sys
# from pymongo import MongoClient
import asyncio
import concurrent.futures


class AccessLogger(AbstractAccessLogger):

    def log(self, request, response, time):
        self.logger.info(f'[{datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")}] '
                         f'{request.remote} '
                         f'"{request.method} {request.rel_url}" '
                         f'done in {time}s: {response.status} '
                         f'- "{request.headers.get("User-Agent")}"')


with open('data/bad_subs.json', 'r') as f:
    bad_subs = json.load(f)

with open('data/lgbt_subs.json', 'r') as f:
    lgbt_subs = json.load(f)

with open('data/related_words.json', 'r') as f:
    related_words = json.load(f)

with open('settings.json', 'r') as f:
    settings = json.load(f)


reddit = praw.Reddit(client_secret=settings['client_secret'], client_id=settings['client_id'],
                     username=settings['username'], password=settings['password'],
                     user_agent=settings['user_agent'])

# db_client = MongoClient(settings['mongodb']['host'], settings['mongodb']['port'])
# db = db_client[settings['mongodb']['db']]

executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)


@aiohttp_jinja2.template('home.html.j2')
async def handle_home(request):
    data = {}
    username = request.rel_url.query.get('u')
    if username is not None:
        username = username.strip()
        usr = {
            'name': username,
        }
        data['user'] = usr
    return data


def get_date_since_str(date_str):
    delta = relativedelta(datetime.utcnow(), datetime.utcfromtimestamp(date_str))
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


# blocking reddit query
def query_reddit(user):
    data = {}
    username = user
    if username is not None:
        username = username.strip()
        u = reddit.redditor(username)
        try:
            u.id
        except NotFound:
            return {'error': 'no_user'}
        c_lgbt = []
        c_bad = []
        c_related = []
        c_t = 0
        p_t = 0
        handled_ids = []
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
            if subname in lgbt_subs:
                c_lgbt.append(c_data)
                handled_ids.append(comment.id)
            if subname in bad_subs:
                c_bad.append(c_data)
                handled_ids.append(comment.id)
            if comment.id not in handled_ids:
                if any(word in comment.body.split() for word in related_words):
                    c_related.append(c_data)

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
            if subname in lgbt_subs:
                c_lgbt.append(p_data)
                handled_ids.append(post.id)
            if subname in bad_subs:
                c_bad.append(p_data)
                handled_ids.append(post.id)
            if post.id not in handled_ids:
                if any(word.lower() in post.selftext.split() for word in related_words['words']) or \
                        subname in related_words['subs']:
                    c_related.append(p_data)

        c_lgbt = sorted(c_lgbt, key=lambda d: d['date'], reverse=True)
        c_bad = sorted(c_bad, key=lambda d: d['date'], reverse=True)
        c_related = sorted(c_related, key=lambda d: d['date'], reverse=True)
        usr = {
            'name': u.name,
            'account_age': get_date_since_str(u.created_utc),
            'profile_pic': u.icon_img,
            'comment_karma': u.comment_karma,
            'link_karma': u.link_karma,
            'good': c_lgbt,
            'flag': c_bad,
            'related': c_related,
            'description': u.subreddit.get('public_description')
        }
        data['user'] = usr
        data['comment_count'] = c_t
        data['post_count'] = p_t
    return data


@aiohttp_jinja2.template('list.html.j2')
async def handle_load_list(request):
    user = request.rel_url.query.get('u')
    completed, pending = await asyncio.wait([asyncio.get_event_loop().run_in_executor(executor, query_reddit, user)])
    results = [t.result() for t in completed]
    return results[0]


@aiohttp_jinja2.template('config.html.j2')
async def handle_show_settings(request):
    return {
        "lgbt_subs": lgbt_subs,
        "flag_subs": bad_subs
    }

app = web.Application()
aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader('templates'))
app.add_routes([web.get('/', handle_home),
                web.get('/config/', handle_show_settings),
                web.get('/ajax/user', handle_load_list)])
app.router.add_static('/static/',
                      path=str(path.join(path.dirname(__file__), 'static/')),
                      name='static')
app.logger.setLevel(logging.INFO)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, handlers=[logging.FileHandler('access.log')])
    web.run_app(app, port=settings['port'], access_log_class=AccessLogger)
