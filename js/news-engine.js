// Nepal News Hub Pro v2 data engine.
// Prefer the server-generated /news.json. Fall back to the existing RSS worker if unavailable.
(function () {
    const STATIC_NEWS_URL = './news.json?ts=' + Math.floor(Date.now() / 300000);
    const STATIC_CACHE_KEY = 'nepal_hub_static_news_v2';

    function normalize(items) {
        return (Array.isArray(items) ? items : [])
            .filter(i => i && i.title && i.link)
            .map(i => ({
                title: String(i.title).trim(),
                link: String(i.link).trim(),
                pubDate: i.pubDate || new Date().toISOString(),
                source: i.source || 'NEWS',
                sourceUrl: i.sourceUrl || '',
                category: i.category || 'nepal',
                thumb: i.thumb || 'https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=900&q=80',
                desc: i.desc || ''
            }));
    }

    function merge(items) {
        const map = new Map();
        [...items, ...(Array.isArray(allNews) ? allNews : [])].forEach(item => {
            if (item && item.link && !map.has(item.link)) map.set(item.link, item);
        });
        allNews = Array.from(map.values()).sort((a, b) => new Date(b.pubDate || 0) - new Date(a.pubDate || 0));
        localStorage.setItem(CACHE_KEY, JSON.stringify(allNews.slice(0, 500)));
        updateHeaderCount();
        renderTab(currentTab);
    }

    async function loadStaticNews() {
        try {
            const response = await fetch(STATIC_NEWS_URL, { cache: 'no-store' });
            if (!response.ok) throw new Error('news.json HTTP ' + response.status);
            const payload = await response.json();
            const items = normalize(payload.items);
            if (!items.length) throw new Error('news.json contained no stories');
            localStorage.setItem(STATIC_CACHE_KEY, JSON.stringify(payload));
            merge(items);
            window.NepalNewsEngine = {
                mode: 'static',
                updatedAt: payload.updatedAt || null,
                count: items.length,
                failures: payload.failedSources || []
            };
            document.documentElement.dataset.newsEngine = 'static';
            return true;
        } catch (error) {
            console.warn('Static news feed unavailable:', error);
            try {
                const cached = JSON.parse(localStorage.getItem(STATIC_CACHE_KEY) || 'null');
                const items = normalize(cached && cached.items);
                if (items.length) {
                    merge(items);
                    window.NepalNewsEngine = { mode: 'cache', updatedAt: cached.updatedAt || null, count: items.length };
                    document.documentElement.dataset.newsEngine = 'cache';
                    return true;
                }
            } catch (_) {}
            return false;
        }
    }

    // Override the old rss2json-heavy worker. This removes the primary cause of empty feeds.
    window.setupWorker = function () {
        loadStaticNews().then(ok => {
            if (!ok && typeof fallbackDirectFetch === 'function') fallbackDirectFetch();
        });
    };

    window.getNewsEngineStatus = function () {
        return window.NepalNewsEngine || { mode: 'starting', count: allNews.length };
    };
})();
