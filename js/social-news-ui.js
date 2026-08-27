(() => {
  const style = document.createElement('style');
  style.textContent = `
  .social-strip{display:flex;gap:14px;overflow-x:auto;padding:4px 2px 14px;scrollbar-width:none}.social-strip::-webkit-scrollbar{display:none}
  .story-bubble{flex:0 0 76px;text-align:center;font-size:10px;font-weight:800;color:#475569}.story-ring{width:68px;height:68px;margin:auto;border-radius:50%;padding:3px;background:linear-gradient(135deg,#f43f5e,#f97316,#facc15)}.story-ring img,.story-fallback{width:100%;height:100%;border-radius:50%;object-fit:cover;background:#e2e8f0;display:flex;align-items:center;justify-content:center;font-weight:900;color:#475569}.reel-modal{position:fixed;inset:0;z-index:100;background:#020617;display:none;align-items:center;justify-content:center}.reel-modal.open{display:flex}.reel-feed{height:100%;width:min(100%,520px);overflow-y:auto;scroll-snap-type:y mandatory}.reel{height:100dvh;scroll-snap-align:start;position:relative;display:flex;align-items:flex-end;background:#111827}.reel img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;opacity:.68}.reel:after{content:'';position:absolute;inset:35% 0 0;background:linear-gradient(transparent,rgba(0,0,0,.92))}.reel-copy{position:relative;z-index:2;color:white;padding:28px 22px 58px;width:100%}.reel-copy h3{font-size:25px;line-height:1.15;font-weight:900;margin:8px 0}.reel-copy p{font-size:13px;color:#cbd5e1}.reel-close{position:fixed;z-index:110;top:18px;right:18px;width:42px;height:42px;border-radius:50%;background:#ffffff22;color:white;font-size:22px}.reel-hint{position:absolute;z-index:3;top:74px;left:0;right:0;text-align:center;color:#fff9;font-size:11px;font-weight:800;pointer-events:none}
  `;document.head.appendChild(style);

  const wait = setInterval(() => {
    if (!window.allNews && !document.getElementById('feed')) return;
    clearInterval(wait); init();
  }, 100);

  function init(){
    const main=document.querySelector('main'); if(!main)return;
    const section=document.createElement('section'); section.id='socialNews';
    section.innerHTML=`<div class="flex items-center justify-between mb-3"><div><p class="text-[10px] font-black uppercase tracking-widest text-rose-600">Social News</p><h2 class="text-xl font-black">Stories & Reels</h2></div><button id="openReels" class="px-4 py-2 rounded-full bg-slate-900 text-white text-xs font-black">▶ Watch Reels</button></div><div id="storyStrip" class="social-strip"></div>`;
    main.insertBefore(section,main.children[1]);
    const modal=document.createElement('div'); modal.className='reel-modal'; modal.id='reelModal'; modal.innerHTML=`<button class="reel-close" id="closeReels">×</button><div class="reel-feed" id="reelFeed"></div><div class="reel-hint">SWIPE UP FOR NEXT NEWS ↑</div>`;document.body.appendChild(modal);
    document.getElementById('openReels').onclick=()=>{buildReels();modal.classList.add('open');document.body.style.overflow='hidden'};
    document.getElementById('closeReels').onclick=()=>{modal.classList.remove('open');document.body.style.overflow=''};
    renderStories();
  }
  function get(){return Array.isArray(window.allNews)?window.allNews:[]}
  function renderStories(){
    const strip=document.getElementById('storyStrip'); if(!strip)return;
    const stories=get().filter(x=>x.title).slice(0,16);strip.innerHTML=stories.map((x,i)=>`<button class="story-bubble" data-story="${i}"><div class="story-ring">${x.thumb?`<img src="${safe(x.thumb)}" loading="lazy">`:`<div class="story-fallback">${esc(x.source||'N')}</div>`}</div><div class="mt-1 truncate">${esc(x.source||'News')}</div></button>`).join('');
    strip.querySelectorAll('[data-story]').forEach(b=>b.onclick=()=>{buildReels();document.getElementById('reelModal').classList.add('open');setTimeout(()=>document.getElementById('reelFeed').children[+b.dataset.story]?.scrollIntoView({behavior:'smooth'}),30);document.body.style.overflow='hidden'});
  }
  function buildReels(){
    const feed=document.getElementById('reelFeed'),items=get().filter(x=>x.title).slice(0,30);feed.innerHTML=items.map(x=>`<article class="reel"><img src="${safe(x.thumb)}" loading="lazy"><div class="reel-copy"><div class="flex gap-2 flex-wrap text-[10px] font-black uppercase"><span>${esc(x.source||'Nepal News')}</span>${x.isBreaking?'<span>🔥 BREAKING</span>':''}${x.sourceCount>1?`<span>• ${x.sourceCount} SOURCES</span>`:''}</div><h3>${esc(x.title)}</h3><p>${esc(x.desc||'Latest news from Nepal.')}</p><a href="${safe(x.link)}" target="_blank" rel="noopener noreferrer" class="inline-block mt-4 bg-white text-slate-900 px-5 py-3 rounded-full text-xs font-black">READ NEWS ↗</a></div></article>`).join('');
  }
  const esc=s=>String(s??'').replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
  const safe=s=>esc(s).replace(/javascript:/gi,'');
})();
