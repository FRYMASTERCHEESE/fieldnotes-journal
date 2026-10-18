"""Build a portable, escaped Markdown journal. Python 3.12+."""
import json, re, shutil, math, os
from pathlib import Path
from datetime import date, datetime, timezone
from html import escape as e
from email.utils import format_datetime
import xml.etree.ElementTree as ET
import markdown
from urllib.parse import quote
from urllib.parse import urlsplit
from html.parser import HTMLParser

class SafeLinks(HTMLParser):
    def __init__(self): super().__init__(convert_charrefs=False); self.output=[]
    def handle_starttag(self,tag,attrs):
        clean=[]
        for name,value in attrs:
            if name in ('href','src'):
                scheme=urlsplit(value or '').scheme.lower()
                if scheme not in ('','http','https','mailto'): continue
            if name.startswith('on'): continue
            clean.append(name if value is None else f'{name}="{e(value,quote=True)}"')
        self.output.append('<'+tag+(' '+' '.join(clean) if clean else '')+'>')
    def handle_endtag(self,tag): self.output.append('</'+tag+'>')
    def handle_data(self,text): self.output.append(text)
    def handle_entityref(self,name): self.output.append('&'+name+';')
    def handle_charref(self,name): self.output.append('&#'+name+';')

def safe_markdown(body):
    parser=SafeLinks();parser.feed(markdown.markdown(e(body),extensions=['extra','sane_lists']));return ''.join(parser.output)

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
        p['html'] = safe_markdown(body)
        p['text'] = body
        posts.append(p)
    return sorted(posts, key=lambda p:p['date'], reverse=True)

def page(title, description, path, content, article=None, noindex=False):
    canonical = URL + '/' + path
    social_image = image_url(article) if article else URL+'/assets/cover-coast.jpg'
    social_alt = article.get('image_alt','Original coastal illustration for Fieldnotes') if article else 'Original coastal illustration for Fieldnotes'
    data = {'@context':'https://schema.org','@type':'BlogPosting' if article else 'WebPage','headline':title,'description':description,'url':canonical}
    if article: data.update(datePublished=article['date'], author={'@type':'Person','name':CONFIG['author']})
    nav = ''.join(f'<a href="{href(p)}"'+(' aria-current="page"' if path==p else '')+f'>{t}</a>' for p,t in [('', 'Journal'),('categories/','Explore'),('about/','About'),('search/','Search'),('studio/','Write')])
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)} — Fieldnotes</title><meta name="description" content="{e(description,quote=True)}"><link rel="canonical" href="{canonical}">
<meta name="theme-color" content="#f7f5ef"><meta property="og:type" content="{'article' if article else 'website'}"><meta property="og:title" content="{e(title,quote=True)}"><meta property="og:description" content="{e(description,quote=True)}"><meta property="og:url" content="{canonical}"><meta property="og:image" content="{e(social_image,quote=True)}"><meta property="og:image:alt" content="{e(social_alt,quote=True)}"><meta name="twitter:card" content="summary_large_image"><meta name="twitter:image" content="{e(social_image,quote=True)}"><meta name="twitter:title" content="{e(title,quote=True)}">
{'<meta name="robots" content="noindex">' if noindex else ''}<link rel="icon" href="{href('assets/favicon.svg')}" type="image/svg+xml"><link rel="stylesheet" href="{href('assets/style.css')}"><link rel="alternate" type="application/rss+xml" title="Fieldnotes RSS" href="{href('feed.xml')}"><script type="application/ld+json">{json.dumps(data).replace('<',chr(92)+'u003c')}</script><script src="{href('assets/app.js')}" defer></script></head><body>
<a class="skip" href="#main" tabindex="0">Skip to content</a><header class="header"><a class="brand" href="{href()}">fieldnotes<span>✳</span></a><nav aria-label="Main navigation">{nav}</nav><a class="rss" href="{href('feed.xml')}">Follow via RSS ↗</a></header>
<main id="main" tabindex="-1">{content}</main><footer><div><a class="brand" href="{href()}">fieldnotes<span>✳</span></a><p>A little curiosity goes a long way.</p></div><nav aria-label="Footer navigation"><a href="{href('about/')}">About</a><a href="{href('contact/')}">Contact</a><a href="{href('privacy/')}">Privacy</a><a href="{href('publishing/')}">Publishing &amp; rights</a><a href="{href('feed.xml')}">RSS feed ↗</a></nav><small>© {date.today().year} FRYMASTERCHEESE · Made for the open web.</small></footer></body></html>'''

def write(path, content):
    target = OUT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding='utf-8')

def image_url(p):
    image = p.get('image', 'assets/cover-coast.jpg')
    if image.startswith('https://github.com/user-attachments/assets/'):
        if not re.fullmatch(r'https://github\.com/user-attachments/assets/[a-zA-Z0-9-]+', image): raise ValueError('Invalid image URL')
        return image
    if not re.fullmatch(r'assets/[a-zA-Z0-9_/-]+\.(?:jpg|jpeg|png|webp)', image): raise ValueError('Invalid image path')
    if not (ROOT/image).is_file(): raise ValueError('Missing image: '+image)
    return URL+'/'+image

def article_cover(p):
    return f'<figure class="article-cover"><img src="{e(image_url(p),quote=True)}" alt="{e(p.get("image_alt","AI-created coastal landscape illustration"),quote=True)}" width="1200" height="630"><figcaption>{e(p.get("image_credit","Original AI-created illustration for Fieldnotes"))} · {e(p.get("image_license","Illustrative artwork, not documentary photography"))}</figcaption></figure>'

def share_tools(p):
    canonical=URL+'/'+p['path']
    caption=p['title']+'\n\n'+p['description']+'\n\n'+canonical
    return f'<aside class="article-share" aria-label="Share this article"><a class="button" href="https://www.facebook.com/sharer/sharer.php?u={quote(canonical,safe="")}" target="_blank" rel="noopener">Share on Facebook ↗</a><button class="button secondary" type="button" data-copy-caption="{e(caption,quote=True)}">Copy Facebook caption</button><p role="status" class="share-status"></p></aside>'

def card(p, index=0, level=3):
    artwork = f'<img src="{e(image_url(p),quote=True)}" alt="" width="1200" height="630" loading="lazy">' if p.get('image') else f'<span>{["✳","◒","↗"][index%3]}</span>'
    return f'''<article class="card"><a class="art art-{index%3}" tabindex="-1" aria-hidden="true" href="{href(p['path'])}">{artwork}</a><div class="meta"><a href="{href('categories/'+p['category_slug']+'/')}">{e(p['category'])}</a> / {p['minutes']} MIN READ</div><h{level}><a href="{href(p['path'])}">{e(p['title'])}</a></h{level}><p>{e(p['description'])}</p><time datetime="{p['date']}">{date.fromisoformat(p['date']).strftime('%d %B %Y')}</time></article>'''

def build():
    if OUT.exists(): shutil.rmtree(OUT)
    OUT.mkdir()
    write('version.json', json.dumps({'revision': os.environ.get('GITHUB_SHA', 'local')}))
    shutil.copytree(ROOT/'assets', OUT/'assets')
    posts=load_posts()
    if not posts: raise ValueError('At least one published article is required')
    featured=posts[0]
    intro='<section class="intro news-intro"><p class="eyebrow">INDEPENDENT VOICES · ORIGINAL PERSPECTIVES</p><h1>Stories that bring<br>the world <em>closer.</em></h1><div class="intro-bottom"><p>Fresh perspectives. Beautiful pictures. Ideas worth sharing.</p><a class="text-link" href="'+href('studio/')+'">Create your story ↗</a></div></section>'
    hero=f'''<section class="feature" aria-label="Featured article"><div class="feature-copy"><p class="eyebrow">THE EDITOR'S PICK / {e(featured['category'])}</p><h2><a href="{href(featured['path'])}">{e(featured['title'])}</a></h2><p>{e(featured['description'])}</p><a class="button" href="{href(featured['path'])}">Read the story ↗</a><p class="meta">{featured['date']} · {featured['minutes']} MIN READ</p></div><div class="feature-photo"><img src="{e(image_url(featured),quote=True)}" alt="{e(featured.get('image_alt','AI-created coastal landscape illustration'),quote=True)}" width="1200" height="630" fetchpriority="high"><p>Original AI-created illustration</p></div></section>'''
    latest='<section id="latest"><div class="section-head"><h2>The latest notes</h2><a href="'+href('categories/')+'">Browse by topic ↗</a></div><div class="grid">'+''.join(card(p,i) for i,p in enumerate(posts))+'</div></section>'
    follow='<aside class="follow"><span class="asterisk">✳</span><div><h2>Good ideas. Your own pace.</h2><p>Follow the journal in your favourite RSS reader. No inbox noise.</p></div><a class="button" href="'+href('feed.xml')+'">Get the RSS feed ↗</a></aside>'
    write('index.html',page('A journal for curious minds',CONFIG['description'],'',intro+hero+latest+follow))
    paths=['','about/','contact/','privacy/','categories/','publishing/']
    for p in posts:
        related=[q for q in posts if q!=p][:2]
        content=f'''<article class="reading"><a class="back" href="{href()}">← Back to the journal</a><p class="eyebrow"><a href="{href('categories/'+p['category_slug']+'/')}">{e(p['category'])}</a></p><h1>{e(p['title'])}</h1><p class="standfirst">{e(p['description'])}</p><div class="byline">By {e(p.get('author',CONFIG['author']))} · <time datetime="{p['date']}">{p['date']}</time> · {p['minutes']} min read</div>{article_cover(p)}<div class="prose">{p['html']}</div>{share_tools(p)}<div class="article-end">✳<p>Thanks for reading. Stay curious.</p><a href="{href('feed.xml')}">Follow future notes via RSS ↗</a></div></article><section><div class="section-head"><h2>Keep exploring</h2></div><div class="grid related">{''.join(card(q,i) for i,q in enumerate(related))}</div></section>'''
        write(p['path']+'index.html',page(p['title'],p['description'],p['path'],content,p)); paths.append(p['path'])
    cats=sorted(set(p['category'] for p in posts))
    catlinks=''.join(f'<a class="topic" href="{href("categories/"+next(p["category_slug"] for p in posts if p["category"]==c)+"/")}">{e(c)} <span>{sum(p["category"]==c for p in posts):02} stories ↗</span></a>' for c in cats)
    write('categories/index.html',page('Explore the journal','Browse all articles by topic.','categories/','<section class="page-title"><p class="eyebrow">FOLLOW YOUR CURIOSITY</p><h1>A few paths<br>to <em>explore.</em></h1>'+catlinks+'</section>'))
    for c in cats:
        group=[p for p in posts if p['category']==c]; path='categories/'+group[0]['category_slug']+'/'
        write(path+'index.html',page(c,'Articles about '+c.lower()+'.',path,'<section class="page-title"><p class="eyebrow">THE JOURNAL / TOPICS</p><h1>'+e(c)+'</h1></section><section class="grid">'+''.join(card(p,i,level=2) for i,p in enumerate(group))+'</section>')); paths.append(path)
    static={
    'about':('A place for curiosity.', '<p>Fieldnotes is an independent journal by FRYMASTERCHEESE, exploring creativity, useful technology, and the small details of everyday life.</p><h2>What you will find here</h2><p>Thoughtful essays, practical experiments, and prompts to see familiar things from a different angle. The emphasis is on useful ideas you can try, rather than a constant stream of updates.</p><h2>A transparent beginning</h2><p>The launch collection was prepared with AI assistance and is presented as introductory editorial content, rather than personal reporting or lived experience. Future articles can be written and edited directly in the public repository.</p><h2>Built for readers</h2><p>No advertisements, tracking scripts, or paywalls. Every article is available on the open web and through the RSS feed.</p>'),
    'contact':('Let’s compare notes.', '<p>Have a question, spotted a mistake, or want to suggest a subject? Open an issue in the journal’s GitHub repository.</p><p><a class="button" href="https://github.com/FRYMASTERCHEESE/fieldnotes-journal/issues/new">Contact via GitHub ↗</a></p><h2>Before you post</h2><p>GitHub issues are public and require a GitHub account. Please share only information you are comfortable making public. Include the article link when reporting a correction. There is no private contact form or email address configured.</p>'),
    'privacy':('A quieter corner of the web.', '<p>Last updated: 18 October 2026.</p><h2>What this website collects</h2><p>This site does not include analytics, advertising, tracking cookies, or visitor accounts. The Author Studio saves draft text in this browser only when you choose Save on this device. You can delete the saved draft in the editor. Selected local pictures are processed on your device and are not uploaded by the editor. GitHub submissions and their attachments are public and governed by GitHub’s policies. Facebook sharing opens Facebook only when you click its share link. Search runs in your browser against a static article index. Your search queries are not submitted to a search service.</p><h2>Hosting and technical logs</h2><p>The site is intended to be hosted on GitHub Pages. GitHub may process IP addresses and technical request information when serving the website under its own policies. See <a href="https://docs.github.com/en/site-policy/privacy-policies/github-privacy-statement">GitHub’s privacy statement</a>.</p><h2>External links and contact</h2><p>When you follow an external link, that website’s policies apply. Public GitHub issues are visible to others. Please do not post private information there.</p><h2>Changes and questions</h2><p>This notice will be updated if the site introduces services that change how visitor information is handled. Questions can be raised through the contact page.</p>')}
    for slug,(title,body) in static.items(): write(slug+'/index.html',page(title,title,slug+'/',f'<article class="reading"><p class="eyebrow">FIELDNOTES / {slug.upper()}</p><h1>{title}</h1><div class="prose">{body}</div></article>'))
    write('studio/index.html',page('Author Studio','Create original picture-led stories for editor review.','studio/',(ROOT/'templates/studio.html').read_text(encoding='utf-8'),noindex=True))
    write('publishing/index.html',page('Publishing and image rights','How approved authors create, review and share original stories.','publishing/',(ROOT/'templates/publishing.html').read_text(encoding='utf-8')))
    search='<section class="page-title"><p class="eyebrow">FIND SOMETHING GOOD</p><h1>Search the <em>journal.</em></h1><form id="search-form" role="search" hidden><label for="query">Search articles by title, topic, or keyword</label><div class="search-row"><input id="query" name="q" type="search" maxlength="200" autocomplete="off"><button class="button" type="submit">Search ↗</button></div></form><p id="search-status" role="status">Search needs JavaScript. You can browse the topics below.</p><div id="results" class="search-results"></div><p><a href="'+href('categories/')+'">Browse every topic instead.</a></p></section>'
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
    print(f'Built {len(posts)} articles and {len(list(OUT.rglob("*.html")))} pages in {OUT}')

if __name__=='__main__': build()
