import json,re,urllib.request
from pathlib import Path
from html import unescape

P=Path('news.json'); data=json.loads(P.read_text(encoding='utf-8'))
HEAD={'User-Agent':'Mozilla/5.0 Nepal-News-Hub-Pro/3.0'}

def get_image(url):
    try:
        req=urllib.request.Request(url,headers=HEAD); raw=urllib.request.urlopen(req,timeout=10).read(250000).decode('utf-8','ignore')
        patterns=[r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)',r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)']
        for p in patterns:
            m=re.search(p,raw,re.I)
            if m:return unescape(m.group(1)).replace('&amp;','&')
    except Exception: pass
    return None

for item in data.get('items',[]):
    if not item.get('thumb') or 'images.unsplash.com' in item.get('thumb',''):
        image=get_image(item.get('link',''))
        if image:item['thumb']=image
P.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
print('Enriched article images from publisher Open Graph metadata')
