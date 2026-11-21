"""Rewrite the Latest writing block in README.md from the Substack feed.

Substack sometimes returns 403 to GitHub's runners, so this falls back to
rss2json. If every source fails, the README is left as it is.
"""
import json
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from email.utils import parsedate_to_datetime

FEED = "https://devanshbuilds.substack.com/feed"
MAX_POSTS = 5
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    return urllib.request.urlopen(req, timeout=30).read()


def from_rss():
    root = ET.fromstring(get(FEED))
    for item in root.iter("item"):
        yield item.findtext("title", ""), item.findtext("link", ""), parsedate_to_datetime(item.findtext("pubDate"))


def from_rss2json():
    url = "https://api.rss2json.com/v1/api.json?rss_url=" + urllib.parse.quote(FEED, safe="")
    data = json.loads(get(url))
    if data.get("status") != "ok":
        raise RuntimeError(data.get("message", "rss2json error"))
    for item in data["items"]:
        yield item["title"], item["link"], datetime.strptime(item["pubDate"], "%Y-%m-%d %H:%M:%S")


posts = []
for source in (from_rss, from_rss2json):
    try:
        posts = list(source())[:MAX_POSTS]
        if posts:
            print(f"got {len(posts)} posts from {source.__name__}")
            break
    except Exception as exc:  # noqa: BLE001
        print(f"{source.__name__} failed: {exc}", file=sys.stderr)

if not posts:
    print("no posts from any source; leaving README alone")
    sys.exit(0)

lines = []
for title, link, date in posts:
    title = title.strip().replace("[", "(").replace("]", ")")
    lines.append(f"- [{title}]({link.strip()}) · {date.strftime('%b')} {date.day}, {date.year}")

with open("README.md", encoding="utf-8") as f:
    readme = f.read()
block = "<!-- SUBSTACK:START -->\n" + "\n".join(lines) + "\n<!-- SUBSTACK:END -->"
new = re.sub(r"<!-- SUBSTACK:START -->.*?<!-- SUBSTACK:END -->", lambda _: block, readme, flags=re.S)
with open("README.md", "w", encoding="utf-8") as f:
    f.write(new)
