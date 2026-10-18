(() => {
  const form = document.querySelector('#search-form');
  if (!form) return;
  const input = document.querySelector('#query');
  const results = document.querySelector('#results');
  const status = document.querySelector('#search-status');
  const site = new URL('../', document.currentScript?.src || document.querySelector('script[src$="app.js"]').src);
  let index;
  let sequence = 0;
  async function search() {
    const request = ++sequence;
    const query = input.value.trim().slice(0, 200);
    const url = new URL(location.href);
    query ? url.searchParams.set('q', query) : url.searchParams.delete('q');
    history.replaceState(null, '', url);
    results.replaceChildren();
    if (!query) { status.textContent = 'Enter a word to start exploring.'; return; }
    status.textContent = 'Searching…';
    try {
      if (!index) {
        const response = await fetch(new URL('search.json', site));
        if (!response.ok) throw new Error('Search unavailable');
        index = await response.json();
      }
      if (request !== sequence) return;
      const terms = query.toLowerCase().split(/\s+/);
      const matches = index.filter(p => terms.every(term => `${p.title} ${p.description} ${p.category} ${p.text}`.toLowerCase().includes(term)));
      status.textContent = `${matches.length} ${matches.length === 1 ? 'story' : 'stories'} found for “${query}”.`;
      matches.forEach(p => {
        const article = document.createElement('article');
        const heading = document.createElement('h2');
        const link = document.createElement('a');
        link.href = new URL(p.path, site).href;
        link.textContent = p.title;
        heading.append(link);
        const description = document.createElement('p');
        description.textContent = p.description;
        article.append(heading, description);
        results.append(article);
      });
    } catch { if (request === sequence) status.textContent = 'Search could not load. Please try again or browse Explore in the navigation.'; }
  }
  form.addEventListener('submit', event => { event.preventDefault(); search(); });
  input.value = new URL(location.href).searchParams.get('q') || '';
  if (input.value) search();
})();
