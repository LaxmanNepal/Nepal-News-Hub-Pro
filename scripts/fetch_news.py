import json
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from html import unescape
from pathlib import Path

FEEDS = {
    "nepal": [
        "https://www.onlinekhabar.com/feed",
        "https://ratopati.com/feed",
        "https://www.setopati.com/feed",
        "https://gorkhapatraonline.com/rss",
        "https://www.annapurnapost.com/rss",
        "https://ujyaaloonline.com/rss",
        "https://nepalpress.com/feed/",
        "https://nepallive.com/feed",
    ],
    "sports": [
        "https://www.hamrokhelkud.com/feed",
        "https://www.cricnepal.com/feed",
        "https://www.goalnepal.com/rss",
    ],
    "finance": [
        "https://www.sharesansar.com/rss",
        "https://clickmandu.com/feed",
        "https://arthasarokar.com/feed",
        "https://bankingkhabar.com/feed",
    ],
    "tech": [
        "https://www.techpana.com/feed",
        "https://www.nepalitelecom.com/feed",
        "https://techmandu.com/feed",
        "https://techsathi.com/feed",
    ],
    "entertainment": [
        "https://www.merofilm.com/feed",
        "https://www.lensnepal.com/feed",
        "https://www.dcnepal.com/category/entertainment/feed",
    ],
}

OUT = Path("news.json")
FALLBACK_IMAGE = "https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=900&q=80"
HEADERS = {"User-Agent": "Nepal-News-Hub-Pro/2.0 (+https://apps.laxmannepal.com.np/)"}


def text(value):
    if value is None:
        return ""
    value = re.sub(r"<script[\s\S]*?</script>|<style[\s\S]*?</style>", " ", value, flags=re.I)
    value = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", unescape(value)).strip()


def first(el, names):
    for name in names:
        node = el.find(name)
        if node is not None and node.text:
            return node.text.strip()
    return ""


def parse_feed(data, feed_url, category):
    root = ET.fromstring(data)
    channel = root.find("channel")
    items = list(channel.findall("item")) if channel is not None else []
    if not items:
        ns_items = root.findall("{http://www.w3.org/2005/Atom}entry")
        items = ns_items

    source = urllib.parse.urlparse(feed_url).hostname or ""
    source = source.removeprefix("www.").split(".")[0].upper()
    results = []
    for item in items[:30]:
        title = first(item, ["title", "{http://www.w3.org/2005/Atom}title"])
        link = first(item, ["link", "{http://www.w3.org/2005/Atom}link"])
        if not link:
            node = item.find("{http://www.w3.org/2005/Atom}link")
            if node is not None:
                link = node.attrib.get("href", "")
        description = first(item, ["description", "summary", "{http://www.w3.org/2005/Atom}summary", "{http://www.w3.org/2005/Atom}content"])
        pub = first(item, ["pubDate", "published", "updated", "{http://www.w3.org/2005/Atom}published", "{http://www.w3.org/2005/Atom}updated"])
        if not title or not link:
            continue
        results.append({
            "title": text(title),
            "link": link.strip(),
            "pubDate": pub.strip() or datetime.now(timezone.utc).isoformat(),
            "source": source,
            "sourceUrl": feed_url,
            "category": category,
            "thumb": FALLBACK_IMAGE,
            "desc": text(description)[:220],
        })
    return results


def fetch(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as response:
        return response.read()


def main():
    merged = {}
    failures = []
    for category, urls in FEEDS.items():
        for url in urls:
            try:
                for item in parse_feed(fetch(url), url, category):
                    key = item["link"]
                    if key not in merged:
                        merged[key] = item
            except Exception as exc:
                failures.append({"url": url, "error": str(exc)[:180]})
            time.sleep(0.15)

    items = list(merged.values())
    items.sort(key=lambda x: x.get("pubDate", ""), reverse=True)
    payload = {
        "version": 2,
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "count": len(items),
        "sourcesAttempted": sum(len(v) for v in FEEDS.values()),
        "failedSources": failures,
        "items": items[:500],
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Generated {len(items)} unique stories from {payload['sourcesAttempted']} feeds; failures={len(failures)}")


if __name__ == "__main__":
    main()
