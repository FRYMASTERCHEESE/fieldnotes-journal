const { test, expect } = require('@playwright/test');
const AxeBuilder = require('@axe-core/playwright').default;
const paths = ['', 'about/', 'privacy/', 'contact/', 'categories/', 'categories/everyday/', 'categories/making/', 'categories/technology/', 'search/', 'studio/', 'publishing/', 'articles/the-art-of-noticing/', 'articles/make-something-small/', 'articles/a-calmer-digital-workspace/', '404.html'];
const url = path => new URL(path, process.env.SITE_URL || 'https://frymastercheese.github.io/fieldnotes-journal/').href;

for (const path of paths) {
  test(`accessibility and responsive layout: ${path || 'home'}`, async ({ page }) => {
    const errors=[];
    page.on('pageerror', err => errors.push(err.message));
    expect((await page.goto(url(path))).status()).toBe(200);
    const audit = await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21a','wcag21aa','wcag22aa','best-practice']).analyze();
    expect(audit.violations.map(v=>({id:v.id,impact:v.impact,nodes:v.nodes.map(n=>({target:n.target,summary:n.failureSummary}))}))).toEqual([]);
    for (const width of [320,390,768,1280]) {
      await page.setViewportSize({width,height:900});
      expect(await page.evaluate(()=>document.documentElement.scrollWidth <= document.documentElement.clientWidth)).toBe(true);
    }
    await page.emulateMedia({reducedMotion:'reduce'});
    await expect.poll(()=>page.evaluate(()=>getComputedStyle(document.documentElement).scrollBehavior)).toBe('auto');
    expect(errors).toEqual([]);
  });
}

test('keyboard skip link and navigation', async ({page,browserName})=>{
  await page.goto(url(''));
  await page.bringToFront();
  await page.keyboard.press('Tab');
  await expect(page.getByRole('link',{name:'Skip to content'})).toBeFocused();
  await page.keyboard.press('Enter');
  await expect(page.locator('main')).toBeFocused();
  await page.getByRole('navigation',{name:'Main navigation'}).getByRole('link',{name:'Explore'}).click();
  await page.getByRole('link',{name:/Technology.*stories/}).click();
  await page.getByRole('heading',{name:'A calmer digital workspace'}).getByRole('link').click();
  await expect(page.getByRole('heading',{level:1})).toHaveText('A calmer digital workspace');
});

test('search results, empty query, no match, URL and safe text', async ({page})=>{
  await page.goto(url('search/?q=workspace'));
  await expect(page.getByRole('status')).toHaveText('1 story found for “workspace”.');
  await expect(page.locator('#results a')).toHaveText('A calmer digital workspace');
  for (const [query, expected] of [['zzzz-no-match','0 stories found'],['<img src=x onerror=alert(1)>','0 stories found'],['','Enter a word']]) {
    await page.getByRole('searchbox').fill(query);
    await page.getByRole('button',{name:'Search ↗'}).click();
    await expect(page.getByRole('status')).toContainText(expected);
    await expect(page.locator('#results img')).toHaveCount(0);
  }
  const audit=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21a','wcag21aa','wcag22aa']).analyze();
  expect(audit.violations).toEqual([]);
});

test('search load failure is announced and retry succeeds',async ({page})=>{
  await page.route('**/search.json',route=>route.abort());
  await page.goto(url('search/?q=workspace'));
  await expect(page.getByRole('status')).toContainText('Search could not load');
  await page.unroute('**/search.json');
  await page.getByRole('button',{name:'Search ↗'}).click();
  await expect(page.getByRole('status')).toContainText('1 story found');
});

test('reading and topics remain usable without JavaScript', async ({browser})=>{
  const context=await browser.newContext({javaScriptEnabled:false});
  const page=await context.newPage();
  await page.goto(url('search/'));
  await expect(page.getByRole('status')).toContainText('Search needs JavaScript.');
  await expect(page.getByRole('searchbox')).toBeHidden();
  await page.getByRole('link',{name:'Browse every topic instead.'}).click();
  await page.getByRole('link',{name:/Making.*stories/}).click();
  await page.getByRole('heading',{name:'Make something small. Finish it well.'}).getByRole('link').click();
  await expect(page.locator('.prose')).toContainText('Describe one complete moment');
  await context.close();
});

test('text resizing and increased text spacing reflow',async ({page})=>{
  for (const path of ['', 'search/', 'studio/', 'articles/the-art-of-noticing/']) {
    await page.goto(url(path));
    await page.setViewportSize({width:320,height:900});
    await page.addStyleTag({content:'html{font-size:200%} *{line-height:1.5!important;letter-spacing:.12em!important;word-spacing:.16em!important} p{margin-bottom:2em!important}'});
    const overflow = await page.evaluate(()=>({width:document.documentElement.clientWidth,scroll:document.documentElement.scrollWidth,elements:[...document.querySelectorAll('body *')].filter(el=>el.getBoundingClientRect().right>document.documentElement.clientWidth+1).map(el=>({tag:el.tagName,class:el.className,right:el.getBoundingClientRect().right}))}));
    expect(overflow.scroll, JSON.stringify(overflow)).toBeLessThanOrEqual(overflow.width);
  }
});

test('author studio prepares a reviewed submission without publishing',async({page})=>{
  await page.goto(url('studio/'));
  await page.getByLabel('Headline',{exact:true}).fill('An original community story');
  await page.getByLabel('Short introduction',{exact:true}).fill('A thoughtful introduction to an original article.');
  await page.getByLabel('Article',{exact:true}).fill('## A fresh perspective\n\n'+ 'This is an original draft for editorial review. '.repeat(8));
  await expect(page.locator('#preview-title')).toHaveText('An original community story');
  await page.getByRole('button',{name:'Save on this device',exact:true}).click();
  await page.reload();
  await page.getByRole('button',{name:'Restore saved draft',exact:true}).click();
  await expect(page.getByLabel('Headline',{exact:true})).toHaveValue('An original community story');
  await page.locator('#rights-check').check();
  await page.getByRole('button',{name:'Prepare editor review ↗'}).click();
  await expect(page.locator('#submission-ready')).toBeVisible();
  const submission=await page.locator('#submission-data').inputValue();
  const data=JSON.parse(submission.match(/```json\n([\s\S]+)\n```/)[1]);
  expect(data.rights_confirmed).toBe(true);
  expect(data.image).toBe('assets/cover-coast.jpg');
  expect(data.slug).toBe('an-original-community-story');
  expect(await page.locator('#submit-link').getAttribute('href')).toContain('/issues/new?');
  await page.getByRole('button',{name:'Delete saved draft',exact:true}).click();
  expect(await page.evaluate(()=>localStorage.getItem('fieldnotes-draft'))).toBeNull();
  await page.getByLabel('Optional: select a photo from your device').setInputFiles('assets/cover-coast.jpg');
  await expect(page.getByRole('button',{name:'Download Facebook picture',exact:true})).toBeEnabled();
  const downloaded=page.waitForEvent('download');
  await page.getByRole('button',{name:'Download Facebook picture',exact:true}).click();
  expect((await downloaded).suggestedFilename()).toBe('an-original-community-story-facebook.jpg');
  const audit=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21a','wcag21aa','wcag22aa','best-practice']).analyze();
  expect(audit.violations).toEqual([]);
});

test('Facebook share contains the published canonical URL',async({page})=>{
  await page.goto(url('articles/the-art-of-noticing/'));
  const link=page.getByRole('link',{name:'Share on Facebook ↗'});
  const shared=new URL(await link.getAttribute('href'));
  expect(shared.origin).toBe('https://www.facebook.com');
  expect(shared.searchParams.get('u')).toBe('https://frymastercheese.github.io/fieldnotes-journal/articles/the-art-of-noticing/');
  expect(await page.locator('[data-copy-caption]').getAttribute('data-copy-caption')).toContain('The quiet art of noticing more');
  const image=await page.locator('meta[property="og:image"]').getAttribute('content');
  expect(image).toMatch(/\.jpg$/);
});

test('RSS, sitemap, robots and assets are served',async ({request})=>{
  for(const path of ['feed.xml','sitemap.xml','robots.txt','search.json','assets/style.css','assets/app.js','assets/favicon.svg']) {
    const response=await request.get(url(path)); expect(response.status()).toBe(200);
    expect((await response.body()).length).toBeGreaterThan(0);
  }
});
