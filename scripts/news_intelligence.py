import json
import re
import unicodedata
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

INPUT = Path('news.json')
NEPALI_STOP = {'को','का','की','मा','ले','बाट','र','पनि','छ','भएको','गरेको','गर्न','देखि','सँग','एक','यो','त्यो','आज','भने','लिएर','सहित','बारे','पछि','अघि','हुन','गर्ने'}
BREAKING_WORDS = {'ब्रेकिङ','तत्काल','आपतकाल','मृत्यु','हताहत','दुर्घटना','भूकम्प','गिरफ्तार','राजीनामा','निर्वाचन','सरकार','आगलागी','बाढी','पहिरो'}
CATEGORIES = ['nepal','politics','finance','sports','tech','entertainment','world']

def normalize(value):
    value = unicodedata.normalize('NFKC', value or '').lower()
    value = re.sub(r'https?://\S+', ' ', value)
    value = re.sub(r'[^\w\u0900-\u097f ]+', ' ', value)
    return re.sub(r'\s+', ' ', value).strip()

def tokens(value):
    return {x for x in normalize(value).split() if len(x) > 2 and x not in NEPALI_STOP}

def similarity(a,b):
    return len(a & b) / max(1, len(a | b))

def score_story(x):
    title = normalize(x.get('title',''))
    words = set(title.split())
    source_count = int(x.get('sourceCount',1) or 1)
    try:
        published = datetime.fromisoformat(x.get('pubDate','').replace('Z','+00:00'))
        age_h = max(0, (datetime.now(timezone.utc)-published).total_seconds()/3600)
    except Exception:
        age_h = 72
    freshness = max(0, 45 - min(45, age_h*1.7))
    breaking = 25 if words & BREAKING_WORDS else 0
    multi = min(25, source_count*7)
    return round(min(100, freshness + breaking + multi),2)

def main():
    data=json.loads(INPUT.read_text(encoding='utf-8'))
    items=data.get('items',[])
    clusters=[]
    for item in items:
        ts=tokens(item.get('title',''))
        match=None
        for cluster in clusters:
            if similarity(ts,cluster['tokens']) >= 0.30:
                match=cluster; break
        if match:
            match['items'].append(item); match['tokens'] |= ts
        else:
            clusters.append({'tokens':set(ts),'items':[item]})

    entities=defaultdict(lambda: {'count':0,'stories':set(),'sources':set()})
    for cluster in clusters:
        stories=cluster['items']
        sources=sorted({x.get('source','') for x in stories if x.get('source')})
        primary=max(stories,key=lambda x:len(x.get('desc','')))
        title=primary.get('title','')
        is_breaking=bool(set(normalize(title).split()) & BREAKING_WORDS) or len(sources)>=3
        category=max((x.get('category','nepal') for x in stories), key=lambda c: sum(1 for x in stories if x.get('category','nepal')==c))
        sid=normalize(title)[:140]
        for story in stories:
            story['storyId']=sid; story['sourceCount']=len(sources); story['relatedSources']=sources
            story['isBreaking']=is_breaking; story['storyCategory']=category; story['importanceScore']=score_story(story)
        # lightweight named-entity extraction for Nepali/Latin capitalized names
        text=' '.join(x.get('title','') for x in stories)
        names=re.findall(r'[A-Z][A-Za-z]{2,}(?:\s+[A-Z][A-Za-z]{2,}){0,2}|[\u0900-\u097F]{2,}(?:\s+[\u0900-\u097F]{2,}){0,1}',text)
        for name in names:
            n=normalize(name)
            if n in NEPALI_STOP or len(n)<3: continue
            entities[n]['count']+=1; entities[n]['stories'].add(sid); entities[n]['sources'].update(sources)

    items.sort(key=lambda x:(x.get('isBreaking',False),x.get('importanceScore',0),x.get('pubDate','')),reverse=True)
    data['version']=4; data['clusters']=len(clusters); data['breakingCount']=sum(1 for x in items if x.get('isBreaking'))
    data['items']=items
    data['intelligence']={'engine':'Nepal News Intelligence v4','updatedAt':datetime.now(timezone.utc).isoformat(),'clusterCount':len(clusters),'sourceCount':len({x.get('source') for x in items if x.get('source')}),'entityCount':len(entities)}
    INPUT.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    Path('data/entities.json').parent.mkdir(exist_ok=True)
    ent=[{'name':k,'count':v['count'],'storyCount':len(v['stories']),'sourceCount':len(v['sources'])} for k,v in entities.items() if v['count']>1]
    ent.sort(key=lambda x:(x['count'],x['sourceCount']),reverse=True)
    Path('data/entities.json').write_text(json.dumps({'updatedAt':datetime.now(timezone.utc).isoformat(),'entities':ent[:100]},ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'Intelligence v4: {len(items)} stories, {len(clusters)} clusters, {len(ent)} entities')

if __name__=='__main__': main()
