import json
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone

p=Path('news.json'); d=json.loads(p.read_text(encoding='utf-8')); items=d.get('items',[])
clusters={}
for x in items:
    sid=x.get('storyId') or x.get('title','').strip().lower()
    clusters.setdefault(sid,[]).append(x)
rows=[]
for sid, group in clusters.items():
    best=max(group,key=lambda x: len(x.get('desc','')))
    sources=sorted({x.get('source','') for x in group if x.get('source')})
    score=min(100, len(sources)*22 + (15 if any(x.get('isBreaking') for x in group) else 0) + min(30,len(group)*2))
    rows.append({'storyId':sid,'title':best.get('title',''),'desc':best.get('desc',''),'thumb':best.get('thumb',''),'category':best.get('storyCategory',best.get('category','nepal')),'sourceCount':len(sources),'sources':sources,'score':score,'isBreaking':any(x.get('isBreaking') for x in group),'link':best.get('link',''),'pubDate':best.get('pubDate','')})
rows.sort(key=lambda x:(x['isBreaking'],x['score'],x['pubDate']),reverse=True)
out={'updatedAt':datetime.now(timezone.utc).isoformat(),'trending':rows[:30]}
Path('data/trending.json').parent.mkdir(exist_ok=True); Path('data/trending.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print(f'Built {len(out["trending"])} trending clusters')
