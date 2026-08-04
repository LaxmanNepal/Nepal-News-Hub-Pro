const RSS_PROXY = "https://api.rss2json.com/v1/api.json?rss_url=";
const CACHE_KEY = "nepal_hub_pro_v4_cache";
const THUMB_PREF_KEY = "nepal_hub_thumb_visible";

let allNews = [];
let currentTab = 'home';
let activeCategory = 'all';
let itemsToShow = 10;
let isBatchLoading = false;
let searchQuery = "";

// Thumbnail state (default: hide)
let showThumbnails = localStorage.getItem(THUMB_PREF_KEY) === 'true';

async function init() {
    updateClock();
    setInterval(updateClock, 1000);
    loadCache();
    setupSearch();
    setupThumbToggle();
    setupScrollListener();
    setupInfiniteScroll();
    
    fetchBatch(MASTER_FEEDS.all.slice(0, 8), 'all');
    switchTab('home');
}

function setupThumbToggle() {
    const toggle = document.getElementById('thumb-toggle');
    toggle.checked = showThumbnails;
    toggle.onchange = (e) => {
        showThumbnails = e.target.checked;
        localStorage.setItem(THUMB_PREF_KEY, showThumbnails);
        renderTab(currentTab);
    };
}

function loadCache() {
    const cached = localStorage.getItem(CACHE_KEY);
    if (cached) {
        allNews = JSON.parse(cached);
        updateCountDisplay();
    }
}

function saveCache() {
    localStorage.setItem(CACHE_KEY, JSON.stringify(allNews.slice(0, 300)));
}

function updateClock() {
    const now = new Date();
    document.getElementById('current-time').innerText = now.toLocaleTimeString('en-GB');
    document.getElementById('current-date').innerText = now.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
}

async function fetchBatch(feedUrls, category) {
    if (isBatchLoading) return;
    isBatchLoading = true;
    
    const promises = feedUrls.map(url => 
        fetch(RSS_PROXY + encodeURIComponent(url))
        .then(r => r.json())
        .then(json => json.status === 'ok' ? json.items.map(i => cleanItem(i, url, category)) : [])
        .catch(() => [])
    );

    const results = await Promise.all(promises);
    const freshItems = results.flat();
    
    const existingLinks = new Set(allNews.map(n => n.link));
    const unique = freshItems.filter(i => !existingLinks.has(i.link));
    
    if (unique.length > 0) {
        allNews = [...unique, ...allNews].sort((a,b) => new Date(b.pubDate) - new Date(a.pubDate));
        saveCache();
        updateCountDisplay();
        renderTab(currentTab);
    }
    isBatchLoading = false;
}

function cleanItem(item, url, category) {
    let thumb = item.thumbnail || item.enclosure?.link;
    if (!thumb) {
        const combined = (item.content || "") + (item.description || "");
        const match = combined.match(/<img[^>]+src="([^">]+)"/);
        if (match && match[1]) thumb = match[1];
    }
    if (!thumb || thumb.includes('avatar') || thumb.length < 10) {
        thumb = `https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=600&q=80`;
    }

    const sourceName = url.replace(/^https?:\/\//, '').replace(/^www\./, '').split('/')[0].split('.')[0].toUpperCase();
    
    return {
        title: item.title,
        link: item.link,
        pubDate: item.pubDate,
        source: sourceName,
        category: category,
        thumb: thumb,
        desc: (item.description || "").replace(/<[^>]*>/g, '').substring(0, 100).trim() + '...'
    };
}

function formatPubDate(dateStr) {
    const pub = new Date(dateStr);
    const now = new Date();
    const diffMin = Math.floor((now - pub) / 60000);
    const diffHrs = Math.floor(diffMin / 60);
    if (diffMin < 60) return `${Math.max(1, diffMin)}m ago`;
    if (diffHrs < 24) return `${diffHrs}h ago`;
    return pub.toLocaleDateString([], { month: 'short', day: 'numeric' });
}

function updateCountDisplay() {
    document.getElementById('header-count').innerText = `${allNews.length} News`;
}

function setCategory(cat) {
    activeCategory = cat;
    document.querySelectorAll('.category-pill').forEach(el => el.classList.remove('active'));
    document.getElementById(`cat-${cat}`).classList.add('active');
    itemsToShow = 10;
    const sample = MASTER_FEEDS[cat].sort(() => 0.5 - Math.random()).slice(0, 5);
    fetchBatch(sample, cat);
    renderTab('home');
    scrollToTop();
}

function switchTab(tab) {
    currentTab = tab;
    itemsToShow = 10;
    document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
    if (document.getElementById(`nav-${tab}`)) document.getElementById(`nav-${tab}`).classList.add('active');
    
    document.getElementById('category-bar').style.display = tab === 'home' ? 'flex' : 'none';
    document.getElementById('thumb-toggle-area').style.display = tab === 'home' ? 'flex' : 'none';
    document.getElementById('app-header').style.display = tab === 'reels' ? 'none' : 'flex';
    
    renderTab(tab);
    scrollToTop();
}

function renderTab(tab) {
    const container = document.getElementById('content-area');
    let data = allNews;

    if (activeCategory !== 'all' && tab === 'home') data = data.filter(i => i.category === activeCategory);
    if (searchQuery) {
        const q = searchQuery.toLowerCase();
        data = data.filter(i => i.title.toLowerCase().includes(q) || i.source.toLowerCase().includes(q));
    }

    switch(tab) {
        case 'home':
            container.innerHTML = `
                <div class="p-4">
                    <h2 class="text-xl font-black text-slate-900 mb-6 flex items-center gap-2">
                        <span class="w-1.5 h-6 bg-rose-600 rounded-full"></span>
                        ${activeCategory === 'all' ? 'Latest Feed' : activeCategory.charAt(0).toUpperCase() + activeCategory.slice(1)}
                    </h2>
                    <div class="space-y-6">
                        ${data.length > 0 ? data.slice(0, itemsToShow).map(item => newsCard(item)).join('') : 
                          `<div class="py-20 text-center"><div class="spinner mx-auto mb-4"></div><p class="text-slate-400 font-bold uppercase text-[10px] tracking-widest">Refreshing News...</p></div>`}
                    </div>
                </div>
            `;
            break;
        case 'reels':
            container.innerHTML = `<div class="reels-container">${allNews.filter(n => !n.thumb.includes('unsplash')).slice(0, 15).map(item => reelCard(item)).join('')}</div>`;
            break;
        case 'sources':
            const uniqueSources = Array.from(new Set(Object.values(MASTER_FEEDS).flat().map(url => url.replace(/^https?:\/\//, '').replace(/^www\./, '').split('/')[0].split('.')[0].toUpperCase()))).sort();
            container.innerHTML = `<div class="p-5"><h2 class="text-xl font-black mb-6 flex items-center gap-2"><span class="w-1.5 h-6 bg-rose-600 rounded-full"></span>Verified Sources</h2><div class="grid grid-cols-2 gap-4">${uniqueSources.map(source => `<div class="source-grid-item animate-in border border-slate-100 shadow-sm"><div class="w-12 h-12 bg-white rounded-2xl shadow-sm flex items-center justify-center mb-3 border border-slate-50"><span class="text-rose-600 font-black text-xl">${source.charAt(0)}</span></div><span class="text-[10px] font-black text-slate-800 uppercase tracking-tighter">${source}</span></div>`).join('')}</div></div>`;
            break;
        case 'notifications':
            container.innerHTML = `<div class="p-5"><h2 class="text-xl font-black mb-6 flex items-center gap-2"><span class="w-1.5 h-6 bg-rose-600 rounded-full"></span>Breaking Alerts</h2><div class="space-y-4">${allNews.slice(0, 15).map(item => `<div class="flex gap-4 p-4 bg-rose-50/40 rounded-2xl border border-rose-100/50 animate-in"><div class="shrink-0 w-2 h-2 mt-2 bg-rose-600 rounded-full shadow-[0_0_8px_rgba(225,29,72,0.6)]"></div><div class="flex-1"><p class="text-[9px] font-black text-rose-600 uppercase mb-1 tracking-widest">${item.source} • ${formatPubDate(item.pubDate)}</p><h3 class="font-bold text-[13px] text-slate-900 leading-tight">${item.title}</h3></div></div>`).join('')}</div></div>`;
            break;
    }
}

function newsCard(item) {
    const thumbHtml = showThumbnails ? `
        <div class="relative h-56">
            <img src="${item.thumb}" class="w-full h-full object-cover" onerror="this.src='https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=600&q=80'">
            <div class="absolute top-5 left-5 px-3 py-1.5 bg-white/95 backdrop-blur rounded-full text-[9px] font-black uppercase tracking-widest text-rose-600 shadow-sm border border-slate-100">
                ${item.source}
            </div>
        </div>` : '';

    return `
        <div class="bg-white rounded-[2rem] overflow-hidden border border-slate-100 shadow-sm animate-in">
            ${thumbHtml}
            <div class="p-6">
                <div class="flex items-center gap-2 mb-3">
                    ${!showThumbnails ? `<span class="px-2 py-0.5 bg-slate-100 rounded text-[8px] font-black uppercase text-rose-600">${item.source}</span>` : ''}
                    <span class="text-[9px] font-black text-slate-400 uppercase tracking-widest">${formatPubDate(item.pubDate)}</span>
                    <span class="w-1 h-1 bg-slate-200 rounded-full"></span>
                    <span class="text-[9px] font-black text-rose-500 uppercase tracking-widest">${item.category}</span>
                </div>
                <h3 class="text-[16px] font-extrabold text-slate-900 mb-3 leading-tight line-clamp-2">${item.title}</h3>
                <p class="text-[12px] text-slate-500 font-medium mb-5 line-clamp-2 leading-relaxed">${item.desc}</p>
                <button onclick="window.open('${item.link}', '_blank')" class="w-full text-[10px] font-black bg-slate-900 text-white py-3 rounded-xl flex items-center justify-center gap-2 uppercase tracking-[0.15em] transition-all active:scale-95">
                    Read Full Article
                    <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M14 5l7 7-7 7"/></svg>
                </button>
            </div>
        </div>
    `;
}

function reelCard(item) {
    return `
        <div class="reel-card">
            <img src="${item.thumb}" class="w-full h-full object-cover">
            <div class="absolute inset-0 bg-gradient-to-b from-black/20 via-transparent to-black/95"></div>
            <div class="absolute bottom-16 left-0 right-0 p-8 text-white">
                <div class="flex items-center gap-2 mb-4">
                   <div class="w-8 h-8 rounded-xl bg-rose-600 flex items-center justify-center text-[11px] font-black shadow-lg">${item.source.charAt(0)}</div>
                   <p class="text-[10px] font-black uppercase tracking-widest">${item.source} • ${formatPubDate(item.pubDate)}</p>
                </div>
                <h2 class="text-2xl font-black leading-tight mb-8">${item.title}</h2>
                <button onclick="window.open('${item.link}', '_blank')" class="bg-white text-black px-10 py-4 rounded-2xl text-[10px] font-black uppercase tracking-[0.2em] active:scale-90 transition-transform">View Full News</button>
            </div>
        </div>
    `;
}

function setupSearch() {
    const toggle = document.getElementById('search-toggle');
    const container = document.getElementById('search-container');
    const input = document.getElementById('search-input');
    const brand = document.getElementById('brand-area');
    const thumbArea = document.getElementById('thumb-toggle-area');

    toggle.onclick = () => {
        const isHidden = container.classList.contains('hidden');
        if (isHidden) {
            container.classList.remove('hidden');
            brand.classList.add('hidden');
            thumbArea.classList.add('hidden');
            input.focus();
        } else {
            container.classList.add('hidden');
            brand.classList.remove('hidden');
            thumbArea.classList.remove('hidden');
            input.value = "";
            searchQuery = "";
            renderTab(currentTab);
        }
    };

    input.oninput = (e) => {
        searchQuery = e.target.value;
        itemsToShow = 10;
        renderTab(currentTab);
    };
}

function setupScrollListener() {
    window.onscroll = () => {
        const btt = document.getElementById('back-to-top');
        if (window.scrollY > 600 && currentTab === 'home') btt.style.display = 'flex';
        else btt.style.display = 'none';
    };
}

function scrollToTop() {
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function setupInfiniteScroll() {
    const obs = new IntersectionObserver((entries) => {
        if (entries[0].isIntersecting && !isBatchLoading && currentTab === 'home') {
            itemsToShow += 10;
            renderTab(currentTab);
        }
    }, { threshold: 0.1 });
    obs.observe(document.getElementById('infinite-anchor'));
}

window.onload = init;
