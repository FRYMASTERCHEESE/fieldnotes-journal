const { test, expect } = require('@playwright/test');
const AxeBuilder = require('@axe-core/playwright').default;
const paths = ['', 'about/', 'privacy/', 'contact/', 'categories/', 'search/', 'studio/', 'publishing/', '404.html'];
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
  await expect(page.getByText('Categories will appear when you publish your first article.')).toBeVisible();
  await page.getByRole('navigation',{name:'Main navigation'}).getByRole('link',{name:'Write',exact:true}).click();
  await expect(page.getByLabel('Headline',{exact:true})).toBeVisible();
});

test('search results, empty query, no match, URL and safe text', async ({page})=>{
  await page.goto(url('search/?q=workspace'));
  await expect(page.getByRole('status')).toHaveText('0 stories found for “workspace”.');
  await expect(page.locator('#results a')).toHaveCount(0);
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
  await expect(page.getByRole('status')).toContainText('0 stories found');
});

test('reading and topics remain usable without JavaScript', async ({browser})=>{
  const context=await browser.newContext({javaScriptEnabled:false});
  const page=await context.newPage();
  await page.goto(url('search/'));
  await expect(page.getByRole('status')).toContainText('Search needs JavaScript.');
  await expect(page.getByRole('searchbox')).toBeHidden();
  await page.getByRole('link',{name:'Browse every topic instead.'}).click();
  await expect(page.getByText('Categories will appear when you publish your first article.')).toBeVisible();
  await context.close();
});

test('text resizing and increased text spacing reflow',async ({page})=>{
  for (const path of ['', 'search/', 'studio/', 'about/']) {
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

test('blank journal has no published articles or stale entries',async({page,request})=>{
  await page.goto(url(''));
  await expect(page.getByText('No articles published yet.')).toBeVisible();
  await expect(page.locator('article.card')).toHaveCount(0);
  await expect(page.getByRole('link',{name:'Write your first article ↗'})).toBeVisible();
  expect(await (await request.get(url('search.json'))).json()).toEqual([]);
  expect(await (await request.get(url('feed.xml'))).text()).not.toContain('<item>');
  expect(await (await request.get(url('sitemap.xml'))).text()).not.toContain('/articles/');
  for(const slug of ['the-art-of-noticing','make-something-small','a-calmer-digital-workspace']) {
    expect((await request.get(url('articles/'+slug+'/'))).status()).toBe(404);
  }
});

test('RSS, sitemap, robots and assets are served',async ({request})=>{
  for(const path of ['feed.xml','sitemap.xml','robots.txt','search.json','generation-status.json','assets/style.css','assets/app.js','assets/favicon.svg']) {
    const response=await request.get(url(path)); expect(response.status()).toBe(200);
    expect((await response.body()).length).toBeGreaterThan(0);
  }
});

test('AI generation clearly stays inactive without setup',async({page})=>{
  await page.route('**/generation-status.json',route=>route.fulfill({json:{available:false}}));
  await page.goto(url('studio/'));
  await expect(page.locator('#generation-availability')).toContainText('not activated');
  await expect(page.locator('#generate-draft')).toBeDisabled();
  await expect(page.locator('#generation-ready')).toBeHidden();
  await expect(page.getByRole('link',{name:'Owner: activate AI generation'})).toHaveAttribute('href','../publishing/#activate-ai');
});

test('configured topic request prepares data without calling AI from browser',async({page})=>{
  const providerRequests=[];page.on('request',request=>{if(request.url().includes('api.openai.com'))providerRequests.push(request.url());});
  await page.route('**/generation-status.json',route=>route.fulfill({json:{available:true}}));
  await page.goto(url('studio/'));
  await expect(page.locator('#generate-draft')).toBeEnabled();
  await page.getByLabel('What should the article be about?').fill('A welcoming neighbourhood');
  await page.getByLabel('Angle or audience',{exact:false}).fill('A practical guide for local groups');
  await page.locator('#generation-notes').fill('No verified reporting supplied.');
  await page.locator('#generation-billing').check();
  await page.locator('#generate-draft').click();
  const body=await page.locator('#generation-data').inputValue();
  expect(body).toContain('<!-- fieldnotes-ai-generate -->');
  const data=JSON.parse(body.match(/```json\n([\s\S]+)\n```/)[1]);
  expect(data.topic).toBe('A welcoming neighbourhood');expect(data.billing_confirmed).toBe(true);
  await expect(page.locator('#generation-link')).toHaveAttribute('href',/github\.com\/FRYMASTERCHEESE\/fieldnotes-journal\/issues\/new\?/);
  expect(providerRequests).toEqual([]);
  const audit=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21a','wcag21aa','wcag22aa','best-practice']).analyze();
  expect(audit.violations).toEqual([]);
});

test('generated review loads editable content and requires explicit approval',async({page})=>{
  const revision='a'.repeat(40);
  const draft={source_issue:7,image:'assets/generated/ai-7.jpg',title:'An original generated draft',description:'A practical draft that still needs the editor’s review.',body:'## Look a little closer\n\n'+'This is test fixture writing awaiting review. '.repeat(10),category:'Community',image_alt:'An illustrative community landscape',facebook_caption:'A friendly community starts with small steps.',review_notes:['Verify all local claims.']};
  await page.route(`https://raw.githubusercontent.com/FRYMASTERCHEESE/fieldnotes-journal/${revision}/**`,route=>{
    if(route.request().url().endsWith('.jpg'))return route.fulfill({path:'assets/cover-coast.jpg',contentType:'image/jpeg'});
    return route.fulfill({json:draft});
  });
  await page.goto(url(`studio/?review=7&revision=${revision}`));
  await expect(page.locator('#ai-review-status')).toContainText('Draft loaded');
  await expect(page.getByLabel('Headline',{exact:true})).toHaveValue(draft.title);
  await expect(page.locator('#rights-check')).not.toBeChecked();
  await page.getByLabel('Headline',{exact:true}).fill('Edited and checked community story');
  await page.getByLabel('Suggested caption',{exact:true}).fill('My edited Facebook caption.');
  await page.locator('#review-image-alt').fill('An AI-created illustration of a welcoming community');
  await page.locator('#rights-check').check();
  await page.getByRole('button',{name:'Prepare approval to publish ↗'}).click();
  const body=await page.locator('#submission-data').inputValue();
  expect(body).toContain('<!-- fieldnotes-ai-approve -->');
  const data=JSON.parse(body.match(/```json\n([\s\S]+)\n```/)[1]);
  expect(data.source_issue).toBe(7);expect(data.source_revision).toBe(revision);expect(data.title).toBe('Edited and checked community story');expect(data.facebook_caption).toBe('My edited Facebook caption.');expect(data.rights_confirmed).toBe(true);
  await expect(page.locator('#submission-explanation')).toContainText('Only the repository owner');
  const audit=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21a','wcag21aa','wcag22aa','best-practice']).analyze();
  expect(audit.violations).toEqual([]);
});
