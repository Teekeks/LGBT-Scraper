from aiohttp import web
import aiohttp_jinja2
import praw
import jinja2
from os import path
from prawcore.exceptions import NotFound
import json

with open('data/bad_subs.json', 'r') as f:
    bad_subs = json.load(f)

with open('data/lgbt_subs.json', 'r') as f:
    lgbt_subs = json.load(f)

with open('settings.json', 'r') as f:
    settings = json.load(f)


reddit = praw.Reddit(client_secret=settings['client_secret'], client_id=settings['client_id'],
                     username=settings['username'], password=settings['password'],
                     user_agent=settings['user_agent'])


@aiohttp_jinja2.template('home.html.j2')
async def handle_home(request):
    data = {}
    username = request.rel_url.query.get('u')
    if username is not None:
        username = username.strip()
        u = reddit.redditor(username)
        try:
            u.id
        except NotFound:
            return {'error': 'no_user'}
        usr = {
            'name': u.name,
            'comment_karma': u.comment_karma,
            'link_karma': u.link_karma
        }
        data['user'] = usr
    return data


@aiohttp_jinja2.template('list.html.j2')
async def handle_load_list(request):
    data = {}
    username = request.rel_url.query.get('u')
    if username is not None:
        username = username.strip()
        u = reddit.redditor(username)
        try:
            u.id
        except NotFound:
            return {'error': 'no_user'}
        from pprint import pprint

        c_lgbt = []
        c_bad = []
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
                    'date': comment.created_utc
                }
            if subname in lgbt_subs:
                c_lgbt.append(c_data)
            if subname in bad_subs:
                c_bad.append(c_data)

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
                'date': post.created_utc
            }
            if subname in lgbt_subs:
                c_lgbt.append(p_data)
            if subname in bad_subs:
                c_bad.append(p_data)
        c_lgbt = sorted(c_lgbt, key=lambda d: d['date'], reverse=True)
        c_bad = sorted(c_bad, key=lambda d: d['date'], reverse=True)
        usr = {
            'name': u.name,
            'comment_karma': u.comment_karma,
            'link_karma': u.link_karma,
            'good': c_lgbt,
            'flag': c_bad
        }
        data['user'] = usr
        data['comment_count'] = c_t
        data['post_count'] = p_t
    return data

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

if __name__ == '__main__':
    web.run_app(app, port=settings['port'])
