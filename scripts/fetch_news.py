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
    "nepal": ["https://www.onlinekhabar.com/feed","https://ratopati.com/feed","https://www.setopati.com/feed","https://gorkhapatraonline.com/rss","https://www.annapurnapost.com/rss","https://nepalpress.com/feed/","https://nepallive.com/feed","https://english.nepalnews.com/feed/","https://www.khabarhub.com/feed/","https://www.thahakhabar.com/feed/","https://www.makalukhabar.com/feed/","https://baahrakhari.com/feed","https://www.nepalitimes.com/feed/","https://thehimalayantimes.com/feed/","https://www.risingnepaldaily.com/rss","https://myrepublica.nagariknetwork.com/feed","https://www.nagariknetwork.com/feed","https://www.lokaantar.com/feed"],
    "sports": ["https://www.hamrokhelkud.com/feed","https://www.cricnepal.com/feed","https://www.goalnepal.com/rss","https://www.nepalpress.com/category/sports/feed/","https://english.onlinekhabar.com/category/sports/feed"],
    "finance": ["https://www.sharesansar.com/rss","https://clickmandu.com/feed","https://arthasarokar.com/feed","https://bankingkhabar.com/feed","https://bizmandu.com/feed","https://www.bizkhabar.com/feed","https://www.nepalpress.com/category/economy/feed/","https://english.onlinekhabar.com/category/business/feed"],
    "tech": ["https://www.techpana.com/feed","https://www.nepalitelecom.com/feed","https://techmandu.com/feed","https://techsathi.com/feed","https://ictframe.com/feed/","https://www.nepalpress.com/category/technology/feed/","https://english.onlinekhabar.com/category/technology/feed"],
    "entertainment": ["https://www.merofilm.com/feed","https://www.lensnepal.com/feed","https://www.dcnepal.com/category/entertainment/feed","https://www.nepalpress.com/category/entertainment/feed/","https://english.onlinekhabar.com/category/entertainment/feed"],
    "world": ["https://www.onlinekhabar.com/content/category/world/feed","https://english.onlinekhabar.com/category/world/feed","https://ratopati.com/category/world/feed","https://www.nepalpress.com/category/world/feed/"]
}
SOURCE_NAMES={"onlinekhabar":"ONLINEKHABAR","ratopati":"RATOPATI","setopati":"SETOPATI","gorkhapatraonline":"GORKHAPATRA","annapurnapost":"ANNAPURNA POST","nepalpress":"NEPAL PRESS","nepallive":"NEPAL LIVE","nepalnews":"NEPAL NEWS","khabarhub":"KHABARHUB","thahakhabar":"THAHA KHABAR","makalukhabar":"MAKALUKHABAR","baahrakhari":"BAAHRakhari","nepalitimes":"NEPALI TIMES","thehimalayantimes":"THE HIMALAYAN TIMES","risingnepaldaily":"THE RISING NEPAL","myrepublica":"REPUBLICA","nagariknetwork":"NAGARIK","lokaantar":"LOKAANTAR","hamrokhelkud":"HAMROKHELKUD","cricnepal":"CRICNEPAL","goalnepal":"GOALNEPAL","clickmandu":"CLICKMANDU","arthasarokar":"ARTHASAROKAR","bankingkhabar":"BANKING KHABAR","bizmandu":"BIZMANDU","bizkhabar":"BIZKHABAR","techpana":"TECHPANA","nepalitelecom":"NEPALITELECOM","techmandu":"TECHMANDU","techsathi":"TECHSATHI","ictframe":"ICT FRAME","merofilm":"MEROFILM","lensnepal":"LENS NEPAL","dcnepal":"DCNEPAL"}
OUT=Path("news.json")
FALLBACK_IMAGE="https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=900&q=80"
HEADERS={"User-Agent":"Nepal-News-Hub-Pro/3.0 (+https://apps.laxmannepal.com.np/Nepal-News-Hub-Pro/)"}
ATOM="http://www.w3.org/2005/Atom"; MRSS="http://search.yahoo.com/mrss/"

def text(v):
    if v is None:return ""
    v=re.sub(r"<script[\s\S]*?</script>|<style[\s\S]*?</style>"," ",v,flags=re.I);v=re.sub(r"<[^>]+>"," ",v)
    return re.sub(r"\s+"," ",unescape(v)).strip()

def first(el,names):
    for n in names:
        node=el.find(n)
        if node is not None and node.text:return node.text.strip()
    return ""

def attr(el,names,key):
    for n in names:
        node=el.find(n)
        if node is not None and node.attrib.get(key):return node.attrib[key]
    return ""

def parse_feed(data,url,category):
    root=ET.fromstring(data);channel=root.find("channel");items=list(channel.findall("item")) if channel is not None else []
    if not items:items=root.findall(f"{{{ATOM}}}entry")
    host=urllib.parse.urlparse(url).hostname or "";key=host.removeprefix("www.").split(".")[0].lower();source=SOURCE_NAMES.get(key,key.upper());out=[]
    for item in items[:40]:
        title=first(item,["title",f"{{{ATOM}}}title"]);link=first(item,["link",f"{{{ATOM}}}link"])
        if not link:
            node=item.find(f"{{{ATOM}}}link");link=node.attrib.get("href","") if node is not None else ""
        desc=first(item,["description","summary",f"{{{ATOM}}}summary",f"{{{ATOM}}}content"]);pub=first(item,["pubDate","published","updated",f"{{{ATOM}}}published",f"{{{ATOM}}}updated"])
        image=attr(item,["media:content",f"{{{MRSS}}}content","media:thumbnail",f"{{{MRSS}}}thumbnail","enclosure"],"url")
        if title and link:out.append({"title":text(title),"link":link.strip(),"pubDate":pub.strip() or datetime.now(timezone.utc).isoformat(),"source":source,"sourceUrl":url,"category":category,"thumb":image or FALLBACK_IMAGE,"desc":text(desc)[:300]})
    return out

def fetch(url):
    req=urllib.request.Request(url,headers=HEADERS)
    with urllib.request.urlopen(req,timeout=15) as r:return r.read()

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
            time.sleep(.1)
    items=list(merged.values());items.sort(key=lambda x:x.get("pubDate",""),reverse=True)
    payload={"version":3,"updatedAt":datetime.now(timezone.utc).isoformat(),"count":len(items),"sourcesAttempted":attempted,"successfulSources":attempted-len(failures),"failedSources":failures,"items":items[:1000]}
    OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"Generated {len(items)} unique stories from {attempted} feeds; successful={payload['successfulSources']}; failures={len(failures)}")

if __name__=="__main__":main()
