"""Build a portable, escaped Markdown journal. Python 3.12+."""
import json, re, shutil, math
from pathlib import Path
from datetime import date, datetime, timezone
from html import escape as e
from email.utils import format_datetime
import xml.etree.ElementTree as ET
import markdown

ROOT = Path(__file__).parent
CONFIG = json.loads((ROOT / 'site.json').read_text())
URL = CONFIG['url'].rstrip('/')
BASE = '/' + URL.split('/', 3)[3].strip('/') if len(URL.split('/', 3)) > 3 else ''
OUT = ROOT / 'dist'

def href(path=''):
    return BASE + '/' + path

def load_posts():
    posts = []
    for file in (ROOT / 'content').glob('*.md'):
        meta, body = file.read_text(encoding='utf-8').split('\n---\n', 1)
        p = json.loads(meta)
        for key in ('title','description','date','category'):
            if not p.get(key): raise ValueError(f'{file}: missing {key}')
        date.fromisoformat(p['date'])
        if p.get('draft') or p['date'] > date.today().isoformat(): continue
        p['slug'] = file.stem
        if not re.fullmatch('[a-z0-9]+(?:-[a-z0-9]+)*', file.stem): raise ValueError('Invalid slug')
        p['category_slug'] = re.sub('[^a-z0-9]+', '-', p['category'].lower()).strip('-')
        p['path'] = 'articles/' + p['slug'] + '/'
        p['minutes'] = max(1, math.ceil(len(body.split()) / 220))
        p['html'] = markdown.markdown(e(body), extensions=['extra','sane_lists'])
        p['text'] = body
        posts.append(p)
    return sorted(posts, key=lambda p:p['date'], reverse=True)

def page(title, description, path, content, article=None, noindex=False):
    canonical = URL + '/' + path
    data = {'@context':'https://schema.org','@type':'BlogPosting' if article else 'WebPage','headline':title,'description':description,'url':canonical}
    if article: data.update(datePublished=article['date'], author={'@type':'Person','name':CONFIG['author']})
    nav = ''.join(f'<a href="{href(p)}"'+(' aria-current="page"' if path==p else '')+f'>{t}</a>' for p,t in [('', 'Journal'),('categories/','Explore'),('about/','About'),('search/','Search')])
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)} — Fieldnotes</title><meta name="description" content="{e(description,quote=True)}"><link rel="canonical" href="{canonical}">
<meta name="theme-color" content="#f7f5ef"><meta property="og:type" content="{'article' if article else 'website'}"><meta property="og:title" content="{e(title,quote=True)}"><meta property="og:description" content="{e(description,quote=True)}"><meta property="og:url" content="{canonical}"><meta property="og:image" content="{URL}/assets/social.svg"><meta name="twitter:card" content="summary"><meta name="twitter:title" content="{e(title,quote=True)}">
{'<meta name="robots" content="noindex">' if noindex else ''}<link rel="icon" href="{href('assets/favicon.svg')}" type="image/svg+xml"><link rel="stylesheet" href="{href('assets/style.css')}"><link rel="alternate" type="application/rss+xml" title="Fieldnotes RSS" href="{href('feed.xml')}"><script type="application/ld+json">{json.dumps(data).replace('<',chr(92)+'u003c')}</script><script src="{href('assets/app.js')}" defer></script></head><body>
<a class="skip" href="#main">Skip to content</a><header class="header"><a class="brand" href="{href()}">fieldnotes<span>✳</span></a><nav aria-label="Main navigation">{nav}</nav><a class="rss" href="{href('feed.xml')}">Follow via RSS ↗</a></header>
<main id="main" tabindex="-1">{content}</main><footer><div><a class="brand" href="{href()}">fieldnotes<span>✳</span></a><p>A little curiosity goes a long way.</p></div><nav aria-label="Footer navigation"><a href="{href('about/')}">About</a><a href="{href('contact/')}">Contact</a><a href="{href('privacy/')}">Privacy</a><a href="{href('feed.xml')}">RSS feed ↗</a></nav><small>© {date.today().year} FRYMASTERCHEESE · Made for the open web.</small></footer></body></html>'''

def write(path, content):
    target = OUT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding='utf-8')

def card(p, index=0):
    return f'''<article class="card"><a class="art art-{index%3}" tabindex="-1" aria-hidden="true" href="{href(p['path'])}"><span>{['✳','◒','↗'][index%3]}</span></a><div class="meta"><a href="{href('categories/'+p['category_slug']+'/')}">{e(p['category'])}</a> / {p['minutes']} MIN READ</div><h3><a href="{href(p['path'])}">{e(p['title'])}</a></h3><p>{e(p['description'])}</p><time datetime="{p['date']}">{date.fromisoformat(p['date']).strftime('%d %B %Y')}</time></article>'''

def build():
    if OUT.exists(): shutil.rmtree(OUT)
    OUT.mkdir()
    shutil.copytree(ROOT/'assets', OUT/'assets')
    posts=load_posts()
    if not posts: raise ValueError('At least one published article is required')
    featured=posts[0]
    intro='<section class="intro"><p class="eyebrow">AN INDEPENDENT JOURNAL · EST. 2026</p><h1>Stay curious.<br>Look a little <em>closer.</em></h1><div class="intro-bottom"><p>Ideas worth exploring. Things worth making.<br>A journal about noticing more of the world.</p><a class="text-link" href="#latest">Find your next read ↓</a></div></section>'
    hero=f'''<section class="feature" aria-label="Featured article"><div class="feature-copy"><p class="eyebrow">THE EDITOR'S PICK / {e(featured['category'])}</p><h2><a href="{href(featured['path'])}">{e(featured['title'])}</a></h2><p>{e(featured['description'])}</p><a class="button" href="{href(featured['path'])}">Read the story ↗</a><p class="meta">{featured['date']} · {featured['minutes']} MIN READ</p></div><div class="feature-art" role="img" aria-label="Abstract sun above layered hills"><div class="sun"></div><div class="hill one"></div><div class="hill two"></div><span>THE ART OF<br>PAYING ATTENTION</span></div></section>'''
    latest='<section id="latest"><div class="section-head"><h2>The latest notes</h2><a href="'+href('categories/')+'">Browse by topic ↗</a></div><div class="grid">'+''.join(card(p,i) for i,p in enumerate(posts))+'</div></section>'
    follow='<aside class="follow"><span class="asterisk">✳</span><div><h2>Good ideas. Your own pace.</h2><p>Follow the journal in your favourite RSS reader. No inbox noise.</p></div><a class="button" href="'+href('feed.xml')+'">Get the RSS feed ↗</a></aside>'
    write('index.html',page('A journal for curious minds',CONFIG['description'],'',intro+hero+latest+follow))
    paths=['','about/','contact/','privacy/','categories/']
    for p in posts:
        related=[q for q in posts if q!=p][:2]
        content=f'''<article class="reading"><a class="back" href="{href()}">← Back to the journal</a><p class="eyebrow"><a href="{href('categories/'+p['category_slug']+'/')}">{e(p['category'])}</a></p><h1>{e(p['title'])}</h1><p class="standfirst">{e(p['description'])}</p><div class="byline">By {e(CONFIG['author'])} · <time datetime="{p['date']}">{p['date']}</time> · {p['minutes']} min read</div><div class="prose">{p['html']}</div><div class="article-end">✳<p>Thanks for reading. Stay curious.</p><a href="{href('feed.xml')}">Follow future notes via RSS ↗</a></div></article><section><div class="section-head"><h2>Keep exploring</h2></div><div class="grid related">{''.join(card(q,i) for i,q in enumerate(related))}</div></section>'''
        write(p['path']+'index.html',page(p['title'],p['description'],p['path'],content,p)); paths.append(p['path'])
    cats=sorted(set(p['category'] for p in posts))
    catlinks=''.join(f'<a class="topic" href="{href("categories/"+next(p["category_slug"] for p in posts if p["category"]==c)+"/")}">{e(c)} <span>{sum(p["category"]==c for p in posts):02} stories ↗</span></a>' for c in cats)
    write('categories/index.html',page('Explore the journal','Browse all articles by topic.','categories/','<section class="page-title"><p class="eyebrow">FOLLOW YOUR CURIOSITY</p><h1>A few paths<br>to <em>explore.</em></h1>'+catlinks+'</section>'))
    for c in cats:
        group=[p for p in posts if p['category']==c]; path='categories/'+group[0]['category_slug']+'/'
        write(path+'index.html',page(c,'Articles about '+c.lower()+'.',path,'<section class="page-title"><p class="eyebrow">THE JOURNAL / TOPICS</p><h1>'+e(c)+'</h1></section><section class="grid">'+''.join(card(p,i) for i,p in enumerate(group))+'</section>')); paths.append(path)
    static={
    'about':('A place for curiosity.', '<p>Fieldnotes is an independent journal by FRYMASTERCHEESE, exploring creativity, useful technology, and the small details of everyday life.</p><h2>What you will find here</h2><p>Thoughtful essays, practical experiments, and prompts to see familiar things from a different angle. The emphasis is on useful ideas you can try, rather than a constant stream of updates.</p><h2>A transparent beginning</h2><p>The launch collection was prepared with AI assistance and is presented as introductory editorial content, rather than personal reporting or lived experience. Future articles can be written and edited directly in the public repository.</p><h2>Built for readers</h2><p>No advertisements, tracking scripts, or paywalls. Every article is available on the open web and through the RSS feed.</p>'),
    'contact':('Let’s compare notes.', '<p>Have a question, spotted a mistake, or want to suggest a subject? Open an issue in the journal’s GitHub repository.</p><p><a class="button" href="https://github.com/FRYMASTERCHEESE/fieldnotes-journal/issues/new">Contact via GitHub ↗</a></p><h2>Before you post</h2><p>GitHub issues are public and require a GitHub account. Please share only information you are comfortable making public. Include the article link when reporting a correction. There is no private contact form or email address configured.</p>'),
    'privacy':('A quieter corner of the web.', '<p>Last updated: 18 October 2026.</p><h2>What this website collects</h2><p>This site does not include analytics, advertising, cookies, or visitor accounts. Search runs in your browser against a static article index. Your search queries are not submitted to a search service.</p><h2>Hosting and technical logs</h2><p>The site is intended to be hosted on GitHub Pages. GitHub may process IP addresses and technical request information when serving the website under its own policies. See <a href="https://docs.github.com/en/site-policy/privacy-policies/github-privacy-statement">GitHub’s privacy statement</a>.</p><h2>External links and contact</h2><p>When you follow an external link, that website’s policies apply. Public GitHub issues are visible to others. Please do not post private information there.</p><h2>Changes and questions</h2><p>This notice will be updated if the site introduces services that change how visitor information is handled. Questions can be raised through the contact page.</p>')}
    for slug,(title,body) in static.items(): write(slug+'/index.html',page(title,title,slug+'/',f'<article class="reading"><p class="eyebrow">FIELDNOTES / {slug.upper()}</p><h1>{title}</h1><div class="prose">{body}</div></article>'))
    search='<section class="page-title"><p class="eyebrow">FIND SOMETHING GOOD</p><h1>Search the <em>journal.</em></h1><form id="search-form" role="search"><label for="query">Search articles by title, topic, or keyword</label><div class="search-row"><input id="query" name="q" type="search" maxlength="200" autocomplete="off"><button class="button" type="submit">Search ↗</button></div></form><p id="search-status" role="status">Enter a word to start exploring.</p><div id="results" class="search-results"></div><noscript><p>Search needs JavaScript. <a href="'+href('categories/')+'">Browse every topic instead.</a></p></noscript></section>'
    write('search/index.html',page('Search','Find articles in the Fieldnotes journal.','search/',search,noindex=True))
    write('search.json',json.dumps([{k:p[k] for k in ('title','description','category','path','text')} for p in posts]))
    write('404.html',page('This page wandered off','Page not found.','404.html','<section class="page-title"><p class="eyebrow">404 / A SMALL DETOUR</p><h1>This page<br>wandered <em>off.</em></h1><p>Try the journal or search for the story you had in mind.</p><a class="button" href="'+href()+'">Back to the journal ↗</a></section>',noindex=True))
    rss=ET.Element('rss',version='2.0'); channel=ET.SubElement(rss,'channel')
    for tag,text in [('title',CONFIG['title']),('link',URL+'/'),('description',CONFIG['description']),('language','en')]: ET.SubElement(channel,tag).text=text
    for p in posts:
        item=ET.SubElement(channel,'item')
        for tag,text in [('title',p['title']),('link',URL+'/'+p['path']),('guid',URL+'/'+p['path']),('description',p['description']),('category',p['category']),('pubDate',format_datetime(datetime.fromisoformat(p['date']).replace(tzinfo=timezone.utc)))]: ET.SubElement(item,tag).text=text
    write('feed.xml',ET.tostring(rss,encoding='unicode',xml_declaration=True))
    sitemap=ET.Element('urlset',xmlns='http://www.sitemaps.org/schemas/sitemap/0.9')
    for path in paths: ET.SubElement(ET.SubElement(sitemap,'url'),'loc').text=URL+'/'+path
    write('sitemap.xml',ET.tostring(sitemap,encoding='unicode',xml_declaration=True)); write('robots.txt','User-agent: *\nAllow: /\nSitemap: '+URL+'/sitemap.xml\n'); write('.nojekyll','')
    print(f'Built {len(posts)} articles and {len(paths)+2} pages in {OUT}')

if __name__=='__main__': build()
