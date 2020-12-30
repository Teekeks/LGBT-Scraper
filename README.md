# LGBT+ Scraper

https://lgbt-scraper.teekeks.app

This Tool will search a given Reddit or Twitter account for content that might be relevant to the LGBT+ community in both positive and negative ways.

This tool does **not save any data** it collects which means that it can take up to 45 seconds to collect all the required data for accounts with tons of activity on them.

If you find any problems, please report them to me by opening a Github Issue.

## Setup

You need a MongoDB database, a Reddit Bot and a Twitter API access, it is also recommended to use a nginx reverse proxy for HTTPS.

Rename the settings.example.json to settings.json and fill in all required data.

Start it with ``python3.8 ./server.py``

## TODO

### certain

* tumblr scraping

