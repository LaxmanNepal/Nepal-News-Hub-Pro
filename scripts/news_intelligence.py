import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

INPUT = Path("news.json")
OUTPUT = Path("news.json")

NEPALI_STOP = {"को", "का", "की", "मा", "ले", "बाट", "र", "पनि", "छ", "भएको", "गरेको", "गर्न", "देखि", "सँग", "एक", "यो", "त्यो", "आज", "भने"}
BREAKING_WORDS = {"ब्रेकिङ", "तत्काल", "आपतकाल", "मृत्यु", "हताहत", "दुर्घटना", "भूकम्प", "गिरफ्तार", "राजीनामा", "निर्वाचन", "सरकार"}


def normalize(value):
    value = unicodedata.normalize("NFKC", value or "").lower()
    value = re.sub(r"https?://\S+", " ", value)
    value = re.sub(r"[^\w\u0900-\u097f ]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def tokens(value):
    return {x for x in normalize(value).split() if len(x) > 2 and x not in NEPALI_STOP}


def similarity(a, b):
    if not a or not b:
        return 0.0
    return len(a & b) / max(1, len(a | b))


def main():
    data = json.loads(INPUT.read_text(encoding="utf-8"))
    items = data.get("items", [])
    clusters = []
    for item in items:
        ts = tokens(item.get("title", ""))
        match = None
        for cluster in clusters:
            if similarity(ts, cluster["tokens"]) >= 0.34:
                match = cluster
                break
        if match:
            match["items"].append(item)
            match["tokens"] |= ts
        else:
            clusters.append({"tokens": set(ts), "items": [item]})

    for cluster in clusters:
        stories = cluster["items"]
        sources = sorted({x.get("source", "") for x in stories if x.get("source")})
        category_counts = defaultdict(int)
        for x in stories:
            category_counts[x.get("category", "nepal")] += 1
        primary = max(stories, key=lambda x: len(x.get("desc", "")))
        title = primary.get("title", "")
        words = set(normalize(title).split())
        is_breaking = bool(words & BREAKING_WORDS) or len(sources) >= 3
        for story in stories:
            story["storyId"] = normalize(title)[:100]
            story["sourceCount"] = len(sources)
            story["relatedSources"] = sources
            story["isBreaking"] = is_breaking
            story["storyCategory"] = max(category_counts, key=category_counts.get)

    items.sort(key=lambda x: (bool(x.get("isBreaking")), x.get("sourceCount", 0), x.get("pubDate", "")), reverse=True)
    data["version"] = max(3, int(data.get("version", 2)))
    data["clusters"] = len(clusters)
    data["breakingCount"] = sum(1 for x in items if x.get("isBreaking"))
    data["items"] = items
    OUTPUT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Intelligence pass: {len(items)} stories, {len(clusters)} clusters, {data['breakingCount']} priority stories")


if __name__ == "__main__":
    main()
