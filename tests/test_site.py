import unittest, json, sys, tempfile
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote, urljoin
import xml.etree.ElementTree as ET
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import build

class Document(HTMLParser):
    def __init__(self, text):
        super().__init__(); self.links=[]; self.ids=set(); self.h1=0; self.meta={}; self.canonical=None; self.feed(text)
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if 'id' in a: self.ids.add(a['id'])
        if tag=='h1': self.h1+=1
        if tag in ('a','link','script','img'):
            value=a.get('href') or a.get('src')
            if value: self.links.append(value)
        if tag=='meta': self.meta[a.get('name',a.get('property'))]=a.get('content')
        if tag=='link' and a.get('rel')=='canonical': self.canonical=a['href']

class SiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): build.build()
    def test_all_internal_links_and_fragments_resolve(self):
        for path in build.OUT.rglob('*.html'):
            doc=Document(path.read_text(encoding='utf-8'))
            for link in doc.links:
                parts=urlsplit(link)
                if parts.scheme or parts.netloc: continue
                parts=urlsplit(urljoin(build.URL+'/'+path.relative_to(build.OUT).as_posix(),link))
                if not parts.path: target=path
                else:
                    self.assertTrue(parts.path.startswith(build.BASE+'/'),link)
                    target=build.OUT / unquote(parts.path[len(build.BASE)+1:])
                    if target.is_dir(): target=target/'index.html'
                self.assertTrue(target.is_file(),f'{path}: {link}')
                if parts.fragment and target.suffix=='.html': self.assertIn(parts.fragment,Document(target.read_text(encoding='utf-8')).ids)
    def test_metadata_and_landmarks(self):
        for path in build.OUT.rglob('*.html'):
            text=path.read_text(encoding='utf-8'); doc=Document(text)
            self.assertEqual(doc.h1,1,path)
            self.assertTrue(doc.meta.get('description'),path)
            self.assertTrue(doc.canonical.startswith(build.URL+'/'))
            self.assertIn('lang="en"',text); self.assertIn('id="main"',text)
            self.assertIn('Skip to content',text)
    def test_feed_and_sitemap(self):
        feed=ET.parse(build.OUT/'feed.xml'); posts=build.load_posts()
        self.assertEqual(len(feed.findall('./channel/item')),len(posts))
        sitemap=ET.parse(build.OUT/'sitemap.xml')
        for loc in sitemap.findall('.//{*}loc'):
            self.assertTrue(loc.text.startswith(build.URL+'/'))
            path=build.OUT / loc.text.removeprefix(build.URL+'/') / 'index.html'
            self.assertTrue(path.exists(),path)
    def test_search_matches_published_content(self):
        index=json.loads((build.OUT/'search.json').read_text())
        self.assertEqual({p['path'] for p in index},{p['path'] for p in build.load_posts()})
        self.assertTrue(all(p['text'] and p['title'] for p in index))
    def test_markdown_blocks_unsafe_link_protocols(self):
        html=build.safe_markdown('[unsafe](javascript:alert(1)) ![bad](data:text/html,test) [safe](https://example.com)')
        self.assertNotIn('href="javascript:',html)
        self.assertNotIn('src="data:',html)
        self.assertIn('href="https://example.com"',html)
    def test_drafts_future_dates_and_unsafe_html(self):
        with tempfile.TemporaryDirectory(dir=build.ROOT) as tmp:
            old=build.ROOT; build.ROOT=Path(tmp); (build.ROOT/'content').mkdir()
            try:
                for slug,extra in [('draft',{'draft':True}),('future',{'date':'2999-01-01'}),('safe',{})]:
                    meta={'title':'Test','description':'Test','category':'Test','date':'2020-01-01',**extra}
                    (build.ROOT/'content'/f'{slug}.md').write_text(json.dumps(meta)+'\n---\n<script>alert(1)</script>')
                posts=build.load_posts(); self.assertEqual(len(posts),1)
                self.assertNotIn('<script>',posts[0]['html'])
            finally: build.ROOT=old

if __name__=='__main__': unittest.main()
