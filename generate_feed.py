
import json
import urllib.request
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path

API_URL = (
    "https://ahundredfallingveils.com/wp-json/wp/v2/posts"
    "?per_page=20&tags_exclude=599304902"
    "&_fields=id,date,title,link,content,tags"
)

class PoemText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "iframe"):
            self.skip += 1
        elif not self.skip and tag in (
            "p", "br", "div", "li", "blockquote", "h1", "h2", "h3"
        ):
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in ("script", "style", "iframe") and self.skip:
            self.skip -= 1
        elif not self.skip and tag in (
            "p", "div", "li", "blockquote", "h1", "h2", "h3"
        ):
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)

    def text(self):
        lines = [line.strip() for line in "".join(self.parts).splitlines()]
        result = "\n".join(line for line in lines if line)
        return result.strip()

def main():
    request = urllib.request.Request(
        API_URL,
        headers={"User-Agent": "DailyPoemRSS/1.0"}
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        posts = json.loads(response.read().decode("utf-8"))

    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")

    ET.SubElement(channel, "title").text = "A Hundred Falling Veils — Poems"
    ET.SubElement(channel, "link").text = "https://ahundredfallingveils.com/"
    ET.SubElement(channel, "description").text = (
        "Recent poems from A Hundred Falling Veils"
    )
    ET.SubElement(channel, "lastBuildDate").text = format_datetime(
        datetime.now(timezone.utc)
    )
    ET.SubElement(channel, "language").text = "en-us"

    for post in posts:
        item = ET.SubElement(channel, "item")
        title = post["title"]["rendered"]
        poem = PoemText()
        poem.feed(post["content"]["rendered"])

        ET.SubElement(item, "title").text = title
        ET.SubElement(item, "link").text = post["link"]
        ET.SubElement(item, "guid").text = post["link"]

        published = datetime.fromisoformat(
            post["date"].replace("Z", "+00:00")
        )
        ET.SubElement(item, "pubDate").text = format_datetime(published)

        ET.SubElement(item, "description").text = poem.text()

    tree = ET.ElementTree(rss)
    ET.indent(tree, space="  ")
    tree.write("feed.xml", encoding="utf-8", xml_declaration=True)

    print(f"Created feed.xml with {len(posts)} posts.")

if __name__ == "__main__":
    main()
