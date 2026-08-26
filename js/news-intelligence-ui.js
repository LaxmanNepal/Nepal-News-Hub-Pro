(() => {
  const originalNewsCard = window.newsCard;
  if (typeof originalNewsCard !== 'function') return;

  window.newsCard = function(item) {
    const card = originalNewsCard(item);
    const meta = `${item.isBreaking ? '<span class="inline-flex items-center gap-1 px-2 py-1 rounded-full bg-rose-50 text-rose-600 border border-rose-100 text-[10px] font-black uppercase">● Breaking</span>' : ''}${item.sourceCount > 1 ? `<span class="inline-flex items-center gap-1 px-2 py-1 rounded-full bg-slate-100 text-slate-600 text-[10px] font-black">${item.sourceCount} sources</span>` : ''}`;
    if (!meta) return card;
    return card.replace(/(<div[^>]*class="[^"]*(?:items-center|flex)[^"]*"[^>]*>)/i, `$1${meta}`);
  };

  window.newsHubIntelligence = {
    rank(items) {
      return [...items].sort((a,b) =>
        Number(b.isBreaking) - Number(a.isBreaking) ||
        (b.sourceCount || 0) - (a.sourceCount || 0) ||
        String(b.pubDate || '').localeCompare(String(a.pubDate || ''))
      );
    },
    summary(item) {
      if (!item) return '';
      if ((item.sourceCount || 0) > 1) return `Reported by ${item.sourceCount} news outlets`;
      return 'Reported by 1 news outlet';
    }
  };
})();
