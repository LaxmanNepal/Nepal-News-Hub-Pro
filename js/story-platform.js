(() => {
  'use strict';
  const esc = (s) => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const safeUrl = (s) => { try { const u = new URL(String(s || ''), location.href); return /^https?:$/.test(u.protocol) ? u.href : '#'; } catch { return '#'; } };
  const state = { story: null };
  const normalize = s => String(s || '').toLowerCase().normalize('NFKC').replace(/[^\p{L}\p{N}\u0900-\u097f ]/gu,' ').replace(/\s+/g,' ').trim();
  const clusterKey = item => item.storyId || normalize(item.title).split(' ').filter(Boolean).slice(0,14).join(' ');
  const grouped = () => {
    const map = new Map();
    (window.allNews || []).forEach(item => {
      const key = clusterKey(item);
      if (!map.has(key)) map.set(key, {key, items: [], sources: new Set(), breaking:false});
      const g = map.get(key); g.items.push(item); if(item.source) g.sources.add(item.source); g.breaking ||= !!item.isBreaking;
    });
    return [...map.values()].map(g => {
      g.items.sort((a,b)=>new Date(b.pubDate||0)-new Date(a.pubDate||0));
      g.sources = [...g.sources];
      g.lead = g.items[0];
      g.score = (g.sources.length*25) + (g.breaking?35:0) + Math.max(0,30-Math.floor((Date.now()-new Date(g.lead.pubDate||0))/3600000));
      return g;
    }).sort((a,b)=>b.score-a.score);
  };
  const ensureModal = () => {
    if (document.getElementById('storyPlatformModal')) return;
    const el = document.createElement('div'); el.id='storyPlatformModal'; el.className='sp-modal';
    el.innerHTML = `<div class="sp-backdrop" data-sp-close></div><section class="sp-dialog" role="dialog" aria-modal="true"><button class="sp-close" data-sp-close aria-label="Close">×</button><div id="spContent"></div></section>`;
    document.body.appendChild(el);
    el.addEventListener('click', e => { if(e.target.matches('[data-sp-close]')) close(); });
  };
  const open = key => {
    const g = grouped().find(x=>x.key===key); if(!g) return;
    ensureModal(); state.story=g; const lead=g.lead;
    document.getElementById('spContent').innerHTML = `<div class="sp-kicker">${g.breaking?'BREAKING STORY':'STORY'} · ${g.sources.length} SOURCES</div><h2>${esc(lead.title)}</h2><p class="sp-summary">${esc(lead.desc || 'Multiple publishers are reporting this story.')}</p><div class="sp-meta">${esc(lead.storyCategory||lead.category||'Nepal')} · ${esc(lead.source||'News source')} · ${esc(lead.pubDate||'')}</div><div class="sp-sources">${g.items.slice(0,10).map((x,i)=>`<a href="${safeUrl(x.link)}" target="_blank" rel="noopener noreferrer"><b>${i+1}</b><span><strong>${esc(x.source||'Source')}</strong><small>${esc(x.title)}</small></span><i>↗</i></a>`).join('')}</div>`;
    document.getElementById('storyPlatformModal').classList.add('open'); document.body.classList.add('sp-locked');
  };
  const close = () => { document.getElementById('storyPlatformModal')?.classList.remove('open'); document.body.classList.remove('sp-locked'); state.story=null; };
  window.openStoryPlatform = open;
  window.closeStoryPlatform = close;
  const install = () => {
    ensureModal();
    const style=document.createElement('style'); style.textContent=`
      .sp-locked{overflow:hidden}.sp-modal{position:fixed;inset:0;z-index:300;display:none}.sp-modal.open{display:block}.sp-backdrop{position:absolute;inset:0;background:#050505b8;backdrop-filter:blur(8px)}.sp-dialog{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);width:min(760px,calc(100vw - 28px));max-height:min(86vh,820px);overflow:auto;background:#fff;color:#111;border-radius:28px;padding:30px;box-shadow:0 30px 100px #0008}.sp-close{position:absolute;right:16px;top:14px;width:40px;height:40px;border:0;border-radius:50%;background:#f4f4f5;font-size:25px}.sp-kicker{font-size:10px;font-weight:900;letter-spacing:.14em;color:#e11d48}.sp-dialog h2{font-family:Inter,'Noto Sans Devanagari',system-ui,sans-serif;font-size:clamp(25px,4vw,42px);line-height:1.08;letter-spacing:-.04em;margin:12px 40px 14px 0}.sp-summary{font-size:14px;line-height:1.7;color:#525252}.sp-meta{font-size:10px;font-weight:800;color:#a3a3a3;margin:16px 0}.sp-sources{border-top:1px solid #e7e5e4}.sp-sources a{display:flex;align-items:center;gap:12px;padding:15px 0;border-bottom:1px solid #e7e5e4;text-decoration:none;color:#111}.sp-sources b{width:28px;height:28px;border-radius:50%;background:#111;color:#fff;display:grid;place-items:center;font-size:11px}.sp-sources span{flex:1}.sp-sources strong{display:block;font-size:11px;color:#e11d48}.sp-sources small{display:block;font-size:11px;line-height:1.4;margin-top:3px}.sp-sources i{font-style:normal;color:#999}@media(max-width:600px){.sp-dialog{padding:22px;border-radius:22px}.sp-dialog h2{font-size:27px}}
    `; document.head.appendChild(style);
  };
  const wire = () => {
    install();
    document.addEventListener('click', e => {
      const card=e.target.closest('.card,.breakcard,.rank'); if(!card || e.target.closest('a,button')) return;
      const title=card.querySelector('h3,h2'); if(!title) return;
      const g=grouped().find(x=>normalize(x.lead.title)===normalize(title.textContent)); if(g) open(g.key);
    });
    const originalRender = window.render;
    if(typeof originalRender==='function'){
      window.render = function(){ originalRender(); setTimeout(enhanceFeed,0); };
      if(window.search) window.search.oninput=window.render;
      setTimeout(enhanceFeed,50);
    }
  };
  const enhanceFeed = () => {
    const feed=document.getElementById('feed'); if(!feed) return;
    const seen=new Set();
    [...feed.children].forEach(card=>{
      const title=card.querySelector('h3'); if(!title) return;
      const g=grouped().find(x=>normalize(x.lead.title)===normalize(title.textContent));
      if(!g) return;
      if(seen.has(g.key)){card.remove();return} seen.add(g.key);
      const body=card.querySelector('.cardbody'); if(body && !body.querySelector('.story-coverage')){ const d=document.createElement('button'); d.className='story-coverage'; d.type='button'; d.textContent=`${g.sources.length} outlets · View story`; d.onclick=()=>open(g.key); body.insertBefore(d, body.querySelector('.cardfoot')); }
    });
  };
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',wire); else wire();
})();
