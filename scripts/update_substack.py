"""Rewrite the Latest writing block in README.md from the Substack RSS feed."""
import re
import urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

FEED = "https://devanshbuilds.substack.com/feed"
MAX_POSTS = 5

req = urllib.request.Request(FEED, headers={"User-Agent": "profile-readme-updater"})
root = ET.fromstring(urllib.request.urlopen(req, timeout=30).read())

lines = []
for item in root.iter("item"):
    title = item.findtext("title", "").strip().replace("[", "(").replace("]", ")")
    link = item.findtext("link", "").strip()
    date = parsedate_to_datetime(item.findtext("pubDate")).strftime("%b %-d, %Y")
    lines.append(f"- [{title}]({link}) · {date}")
    if len(lines) == MAX_POSTS:
        break

if not lines:
    raise SystemExit("feed returned no posts; leaving README alone")

with open("README.md", encoding="utf-8") as f:
    readme = f.read()
block = "<!-- SUBSTACK:START -->\n" + "\n".join(lines) + "\n<!-- SUBSTACK:END -->"
new = re.sub(r"<!-- SUBSTACK:START -->.*?<!-- SUBSTACK:END -->", lambda _: block, readme, flags=re.S)
with open("README.md", "w", encoding="utf-8") as f:
    f.write(new)
