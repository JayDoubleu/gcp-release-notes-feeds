import sys
import json
import logging
import argparse
import requests
from bs4 import BeautifulSoup

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
args = parser.parse_args()

logging.basicConfig(
    level=args.loglevel,
    format="[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s: %(message)s",
    handlers=[
        logging.StreamHandler(stream=sys.stdout),
    ],
)
logger = logging.getLogger()

base_url = "https://cloud.google.com"
url = f"{base_url}/release-notes/all"

try:
    response = requests.get(url)
except requests.exceptions.RequestException as e:
    logger.error(f"Error requesting {url}: {e}")
    sys.exit(1)

soup = BeautifulSoup(response.text, "html.parser")

links = []
links_dict = []

for a in soup.find_all("a", href=True):
    if "/docs/release-notes" in a["href"]:
        html_link = a["href"]
        try:
            response = requests.get(f"{base_url}{html_link}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Error requesting {html_link}: {e}")
            continue

        soup = BeautifulSoup(response.text, "html.parser")
        link = soup.find("link", rel="alternate", type="application/atom+xml")
        if link:
            if link not in links:
                print(f"found { link['href']}")
                links.append(link)
                entry = {"html_url": f"{base_url}{html_link}", "feed_url": link["href"]}
                links_dict.append(entry)

json_str = json.dumps(links_dict, indent=4)

try:
    with open("feeds.json", "w") as f:
        f.write(json_str)
except IOError as e:
    logger.error(f"Error writing to feeds.json: {e}")
    sys.exit(1)
