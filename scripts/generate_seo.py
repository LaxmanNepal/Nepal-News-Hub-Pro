import json, re
from pathlib import Path
from html import escape
from datetime import datetime, timezone

ROOT=Path('.')
data=json.loads((ROOT/'news.json').read_text(encoding='utf-8'))
items=data.get('items',[])
OUT=ROOT/'news-pages'; OUT.mkdir(exist_ok=True)

def slug(s):
    s=re.sub(r'[^\w\u0900-\u097f]+','-',s.lower()).strip('-')
    return s[:110] or 'news'

def page(item):
    title=escape(item.get('title','Nepal News'))
    desc=escape((item.get('desc') or title)[:160])
    url='https://apps.laxmannepal.com.np/Nepal-News-Hub-Pro/news-pages/'+slug(item.get('title','news'))+'.html'
    image=escape(item.get('thumb',''))
    pub=escape(item.get('pubDate',''))
    source=escape(item.get('source','Nepal News Hub'))
    related=''.join(f'<li><a href="{escape(slug(x.get("title","")))}.html">{escape(x.get("title",""))}</a></li>' for x in items if x.get('link')!=item.get('link') and x.get('storyId')==item.get('storyId'))
    return f'''<!doctype html><html lang="ne"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title} | Nepal News Hub Pro</title><meta name="description" content="{desc}"><link rel="canonical" href="{url}"><meta property="og:type" content="article"><meta property="og:title" content="{title}"><meta property="og:description" content="{desc}"><meta property="og:image" content="{image}"><meta property="article:published_time" content="{pub}"><meta property="article:section" content="{escape(item.get('storyCategory',item.get('category','Nepal')))}"><script type="application/ld+json">{json.dumps({'@context':'https://schema.org','@type':'NewsArticle','headline':item.get('title',''),'datePublished':item.get('pubDate'),'image':[item.get('thumb','')],'author':{'@type':'Organization','name':item.get('source','News source')},'publisher':{'@type':'Organization','name':'Nepal News Hub Pro'},'description':item.get('desc',''),'mainEntityOfPage':{'@type':'WebPage','@id':url}},ensure_ascii=False)}</script><style>body{{font-family:system-ui,sans-serif;background:#f8fafc;margin:0;color:#0f172a}}main{{max-width:850px;margin:40px auto;padding:20px}}article{{background:#fff;padding:28px;border-radius:24px;border:1px solid #e2e8f0}}img{{width:100%;max-height:480px;object-fit:cover;border-radius:18px}}a{{color:#e11d48;text-decoration:none}}small{{color:#64748b}}</style></head><body><main><p><a href="../">← Nepal News Hub Pro</a></p><article><small>{source} · {pub}</small><h1>{title}</h1><img src="{image}" alt="{title}" loading="lazy"><p>{desc}</p><p><a href="{escape(item.get('link','#'))}" target="_blank" rel="noopener noreferrer">Read the original report →</a></p>{('<h2>Related reports</h2><ul>'+related+'</ul>') if related else ''}</article></main></body></html>'''

for i,item in enumerate(items):
    name=slug(item.get('title','news'))
    if not name: name=f'news-{i}'
    (OUT/f'{name}.html').write_text(page(item),encoding='utf-8')

urls=['https://apps.laxmannepal.com.np/Nepal-News-Hub-Pro/']+[f'https://apps.laxmannepal.com.np/Nepal-News-Hub-Pro/news-pages/{slug(i.get("title","news"))}.html' for i in items]
xml='<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join(f'<url><loc>{escape(u)}</loc></url>' for u in dict.fromkeys(urls))+'</urlset>'
(ROOT/'sitemap.xml').write_text(xml,encoding='utf-8')
print(f'Generated {len(items)} SEO article pages and sitemap')
