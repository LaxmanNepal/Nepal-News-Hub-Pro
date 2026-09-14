import json
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from html import unescape
from pathlib import Path

FEEDS = {
    "nepal": [
        "https://www.onlinekhabar.com/feed","https://ratopati.com/feed","https://www.setopati.com/feed",
        "https://gorkhapatraonline.com/rss","https://www.annapurnapost.com/rss","https://nepalpress.com/feed/",
        "https://nepallive.com/feed","https://english.nepalnews.com/feed/","https://www.khabarhub.com/feed/",
        "https://www.thahakhabar.com/feed/","https://www.makalukhabar.com/feed","https://baahrakhari.com/feed",
        "https://www.nepalitimes.com/feed/","https://thehimalayantimes.com/feed/","https://www.risingnepaldaily.com/rss",
        "https://myrepublica.nagariknetwork.com/feed","https://www.nagariknetwork.com/feed","https://www.lokaantar.com/feed",
        "https://www.nayapatrikadaily.com/feed","https://www.nepalsamaya.com/feed","https://www.newsofnepal.com/feed",
        "https://hamrakura.com/feed","https://www.nayapage.com/feed","https://onlinetvnepal.com/feed"
    ],
    "sports": [
        "https://www.hamrokhelkud.com/feed","https://www.cricnepal.com/feed","https://www.goalnepal.com/rss",
        "https://www.nepalpress.com/category/sports/feed/","https://english.onlinekhabar.com/category/sports/feed/",
        "https://www.ratopati.com/category/sports/feed"
    ],
    "finance": [
        "https://www.sharesansar.com/rss","https://clickmandu.com/feed","https://arthasarokar.com/feed",
        "https://bankingkhabar.com/feed","https://bizmandu.com/feed","https://www.bizkhabar.com/feed",
        "https://www.nepalpress.com/category/economy/feed/","https://english.onlinekhabar.com/category/business/feed/",
        "https://www.aarthiknews.com/feed","https://newbusinessage.com/feed"
    ],
    "tech": [
        "https://www.techpana.com/feed","https://www.nepalitelecom.com/feed","https://techmandu.com/feed",
        "https://techsathi.com/feed","https://ictframe.com/feed/","https://www.nepalpress.com/category/technology/feed/",
        "https://english.onlinekhabar.com/category/technology/feed/","https://neostuffs.com/feed"
    ],
    "entertainment": [
        "https://www.merofilm.com/feed","https://www.lensnepal.com/feed","https://www.dcnepal.com/category/entertainment/feed",
        "https://www.nepalpress.com/category/entertainment/feed/","https://english.onlinekhabar.com/category/entertainment/feed/",
        "https://www.osnepal.com/feed"
    ],
    "world": [
        "https://www.onlinekhabar.com/content/category/world/feed","https://english.onlinekhabar.com/category/world/feed",
        "https://ratopati.com/category/world/feed","https://www.nepalpress.com/category/world/feed/"
    ]
}
SOURCE_NAMES={"onlinekhabar":"ONLINEKHABAR","ratopati":"RATOPATI","setopati":"SETOPATI","gorkhapatraonline":"GORKHAPATRA","annapurnapost":"ANNAPURNA POST","nepalpress":"NEPAL PRESS","nepallive":"NEPAL LIVE","nepalnews":"NEPAL NEWS","khabarhub":"KHABARHUB","thahakhabar":"THAHA KHABAR","makalukhabar":"MAKALUKHABAR","baahrakhari":"BAAHRakhari","nepalitimes":"NEPALI TIMES","thehimalayantimes":"THE HIMALAYAN TIMES","risingnepaldaily":"THE RISING NEPAL","myrepublica":"REPUBLICA","nagariknetwork":"NAGARIK","lokaantar":"LOKAANTAR","nayapatrikadaily":"NAYA PATRIKA","nepalsamaya":"NEPAL SAMAYA","newsofnepal":"NEWS OF NEPAL","hamrakura":"HAMRAKURA","nayapage":"NAYA PAGE","onlinetvnepal":"ONLINETV NEPAL","hamrokhelkud":"HAMROKHELKUD","cricnepal":"CRICNEPAL","goalnepal":"GOALNEPAL","clickmandu":"CLICKMANDU","arthasarokar":"ARTHASAROKAR","bankingkhabar":"BANKING KHABAR","bizmandu":"BIZMANDU","bizkhabar":"BIZKHABAR","aarthiknews":"AARTHIK NEWS","newbusinessage":"NEW BUSINESS AGE","techpana":"TECHPANA","nepalitelecom":"NEPALITELECOM","techmandu":"TECHMANDU","techsathi":"TECHSATHI","ictframe":"ICT FRAME","neostuffs":"NEOSTUFFS","merofilm":"MEROFILM","lensnepal":"LENS NEPAL","dcnepal":"DCNEPAL","osnepal":"OSNEPAL"}
OUT=Path("news.json")
FALLBACK_IMAGE="https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=1200&q=82"
HEADERS={"User-Agent":"Mozilla/5.0 (compatible; Nepal-News-Hub-Pro/5.0; +https://apps.laxmannepal.com.np/Nepal-News-Hub-Pro/)"}
ATOM="http://www.w3.org/2005/Atom"; MRSS="http://search.yahoo.com/mrss/"

def text(v):
    if v is None:return ""
    v=re.sub(r"<script[\s\S]*?</script>|<style[\s\S]*?</style>"," ",v,flags=re.I);v=re.sub(r"<[^>]+>"," ",v)
    return re.sub(r"\s+"," ",unescape(v)).strip()

def first(el,names):
    for n in names:
        node=el.find(n)
        if node is not None:
            value=node.text or node.attrib.get("href") or ""
            if value:return value.strip()
    return ""

def image_from_item(item):
    candidates=[]
    for node in item.iter():
        tag=node.tag.split("}")[-1].lower()
        if tag in {"content","thumbnail","enclosure","image"}:
            for key in ("url","href","src"):
                if node.attrib.get(key):candidates.append(node.attrib[key])
    html=" ".join([(item.findtext("description") or ""),(item.findtext(f"{{{ATOM}}}summary") or ""),(item.findtext(f"{{{ATOM}}}content") or "")])
    candidates += re.findall(r'<img[^>]+(?:src|data-src)=["\']([^"\']+)',html,re.I)
    for u in candidates:
        u=unescape(u).strip()
        if u.startswith("//"):u="https:"+u
        if u.startswith("http") and not any(x in u.lower() for x in ("avatar","logo","icon","gravatar")):return u
    return ""

def parse_feed(data,url,category):
    root=ET.fromstring(data);channel=root.find("channel");items=list(channel.findall("item")) if channel is not None else []
    if not items:items=root.findall(f"{{{ATOM}}}entry")
    host=urllib.parse.urlparse(url).hostname or "";key=host.removeprefix("www.").split(".")[0].lower();source=SOURCE_NAMES.get(key,key.upper());out=[]
    for item in items[:60]:
        title=first(item,["title",f"{{{ATOM}}}title"]);link=first(item,["link",f"{{{ATOM}}}link"])
        desc=first(item,["description","summary",f"{{{ATOM}}}summary",f"{{{ATOM}}}content"]);pub=first(item,["pubDate","published","updated",f"{{{ATOM}}}published",f"{{{ATOM}}}updated"])
        image=image_from_item(item)
        if title and link:out.append({"title":text(title),"link":link.strip(),"pubDate":pub.strip() or datetime.now(timezone.utc).isoformat(),"source":source,"sourceUrl":url,"category":category,"thumb":image or FALLBACK_IMAGE,"image":image or FALLBACK_IMAGE,"hasImage":bool(image),"desc":text(desc)[:350]})
    return out

def fetch(url):
    req=urllib.request.Request(url,headers=HEADERS)
    with urllib.request.urlopen(req,timeout=15) as r:return r.read()

def enrich_image(item):
    if item.get("hasImage"):return item
    try:
        req=urllib.request.Request(item["link"],headers=HEADERS)
        with urllib.request.urlopen(req,timeout=7) as r:html=r.read(180000).decode("utf-8","ignore")
        patterns=[r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)',r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)']
        for pattern in patterns:
            m=re.search(pattern,html,re.I)
            if m:
                u=unescape(m.group(1)).strip()
                if u.startswith("//"):u="https:"+u
                if u.startswith("http"):
                    item["thumb"]=u;item["image"]=u;item["hasImage"]=True;break
    except Exception:pass
    return item

def main():
    merged={};failures=[];attempted=0
    for category,urls in FEEDS.items():
        for url in urls:
            attempted+=1
            try:
                for item in parse_feed(fetch(url),url,category):
                    key=item["link"].split("#")[0]
                    if key not in merged:merged[key]=item
            except Exception as exc:failures.append({"url":url,"error":str(exc)[:180]})
            time.sleep(.08)
    items=list(merged.values());items.sort(key=lambda x:x.get("pubDate",""),reverse=True)
    # Recover article-level og:image only for the newest image-less stories to keep CI fast.
    targets=items[:180]
    with ThreadPoolExecutor(max_workers=12) as pool:
        futures=[pool.submit(enrich_image,x) for x in targets]
        for f in as_completed(futures):f.result()
    payload={"version":5,"updatedAt":datetime.now(timezone.utc).isoformat(),"count":len(items),"sourcesAttempted":attempted,"successfulSources":attempted-len(failures),"failedSources":failures,"imageCoverage":sum(1 for x in items if x.get("hasImage")),"items":items[:1200]}
    OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"Generated {len(items)} unique stories from {attempted} feeds; successful={payload['successfulSources']}; failures={len(failures)}; images={payload['imageCoverage']}")

if __name__=="__main__":main()
