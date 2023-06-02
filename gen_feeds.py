import sys
import json
import datetime
import logging
import argparse
import pytz
from dateutil import parser
import htmlmin
import requests
import feedparser
import feedgenerator
import xmltodict
import xml.dom.minidom
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
import html2markdown

parser = argparse.ArgumentParser()
parser.add_argument(
    "-d",
    "--debug",
    help="Show debug logs",
    action="store_const",
    dest="loglevel",
    const=logging.DEBUG,
    default=logging.INFO,
)
parser.add_argument(
    "--days-since",
    help="Number of days since last updated to include in feed",
    type=int,
    default=7,
)
args = parser.parse_args()

logging.basicConfig(
    level=args.loglevel,
    format="[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s: %(message)s",
    handlers=[
        logging.StreamHandler(stream=sys.stdout),
    ],
)
logger = logging.getLogger()

with open("feeds.json") as f:
    feed_data = json.load(f)

feed = feedgenerator.Rss201rev2Feed(
    title="My RSS Feed",
    link="http://example.com/rss/",
    description="This is an example RSS feed",
)


def parse_feed(parsed_feed):
    url = parsed_feed["feed_url"]
    logger.info(f"Processing {url}")
    parsed_feed = feedparser.parse(url, sanitize_html=False)
    last_30_days = datetime.datetime.now(pytz.utc) - datetime.timedelta(
        days=args.days_since
    )
    filtered_entries = [
        entry
        for entry in parsed_feed.entries
        if datetime.datetime.strptime(entry.updated, "%Y-%m-%dT%H:%M:%S%z")
        >= last_30_days
    ]
    for entry in filtered_entries:
        description = htmlmin.minify(entry.description, remove_empty_space=True)
        description = html2markdown.convert(description)
        entrydate = datetime.datetime.strptime(entry.updated, "%Y-%m-%dT%H:%M:%S%z")
        feed.add_item(
            title=f"{entry.id} - {entry.title}",
            pubdate=entrydate,
            updateddate=entrydate,
            unique_id=entry.id,
            link=entry.link,
            description=description[:1000],
        )


with ThreadPoolExecutor() as executor:
    executor.map(parse_feed, feed_data)

xml_str = feed.writeString("utf-8")
dom = xml.dom.minidom.parseString(xml_str)
rss_feed = dom.toprettyxml()

with open(f"feeds_combined_last_{args.days_since}_days.xml", "w") as f:
    f.write(rss_feed)
