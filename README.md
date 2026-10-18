# Fieldnotes ✳

An independent editorial journal for FRYMASTERCHEESE. Separate project; no existing repository is required or modified. Static HTML, responsive CSS, browser-local search, Markdown articles, RSS, sitemap, structured metadata, topic archives, and accessible navigation.

## Run locally

Requires Python 3.12 or newer.

```sh
python -m pip install -r requirements.txt
python build.py
python -m unittest discover -s tests -v
python scripts/serve.py
```

Open http://127.0.0.1:8000/fieldnotes-journal/ for a preview using the production project path. No configuration edit is required.

## Publish an article

1. Open `content/` on GitHub and choose **Add file → Create new file**, or work locally on a branch.
2. Name it `your-article-slug.md` using lowercase letters, digits, and hyphens.
3. Start with JSON metadata, a line containing `---`, then Markdown. Example:

```markdown
{"title":"Your article title","description":"A clear one-sentence summary.","date":"2026-10-18","category":"Making","draft":false}
---
Opening paragraph.

## A useful heading

Your article goes here.
```

4. Use `draft:true` to keep a post unpublished. Future-dated posts are excluded using the build machine's date; publication needs a new push or a manual workflow run when that date arrives. Dates are not an automatic scheduler.
5. Preview changes and open a pull request. CI checks content, metadata, feed, sitemap, links and draft handling. Merge to `main` to publish automatically.

The newest article is featured automatically. Categories, reading times, RSS and search index update during the build. Raw HTML in Markdown is escaped. Trusted editors can add Markdown links and should check their destinations before publishing. Images can live in `assets/`; use the production base path `/fieldnotes-journal/assets/filename.jpg` in Markdown.

## First deployment

Repository name: `fieldnotes-journal` under `FRYMASTERCHEESE`.

In **Settings → Pages → Build and deployment → Source**, choose **GitHub Actions**. Then run **Test and publish journal** from the Actions tab or push to `main`. The workflow tests, uploads `dist`, and deploys to the `github-pages` environment. Expected address (not a verification claim): https://frymastercheese.github.io/fieldnotes-journal/

## Configuration and maintenance

- Edit brand, description, production URL, and author in `site.json`. Changing the project path requires updating image links and any hardcoded repository links in the contact page and this README.
- Keep Python and GitHub Actions dependencies updated; Dependabot is configured monthly.
- Launch articles are AI-assisted introductory editorial content, disclosed on the About page. Review them and replace them with your own writing as desired.
- The contact page uses public GitHub issues; it does not deliver private messages. No invented email address, mailing list, analytics, cookies, or backend is configured.
- Article and site social metadata now use a JPEG cover with alt text and large-image preview metadata. Facebook controls its own preview cache.
- No paid service is configured. Custom author image attachments may be served from GitHub. RSS requires a reader; search and the editor require JavaScript. Reading and topic archives work without it.
- Before using a custom domain, update `site.json`, configure GitHub Pages DNS and HTTPS, and rebuild.

## Verification

Automated checks do not replace a full accessibility audit or testing in every browser. Verify mobile layout, keyboard navigation, search, article URLs, RSS, sitemap, and the deployed commit after significant changes.

## Author Studio and Facebook

Open `/studio/` to write and preview a draft, save it on the device, prepare an original or licensed cover, export a Facebook-size JPEG, and prepare an editor submission. The browser does not send drafts until the author follows the GitHub submission link and submits the issue. Local draft backups contain text, not selected local image files.

Approved GitHub usernames and public bylines are maintained in `authors.json`; only FRYMASTERCHEESE is initially approved. Authors do not need repository write access. Keep editor write access restricted. The submissions workflow accepts JSON data from issues bearing its marker, checks the issue author's identity against the allowlist, validates fields and image URLs, then creates a separate draft branch. It attempts to open a review request automatically. If repository settings disable Actions-created pull requests, the issue receives a ready-to-open comparison link for the editor; no setting or credential expansion is required. Never enable automated merging or approvals for editorial content.

The editor verifies original writing, facts, rights, credits and alt text, then merges. The deployment workflow runs build and browser checks before publishing. GitHub does not start pull-request workflows for changes created using GITHUB_TOKEN; run the test workflow on the submission branch manually for checks before merging. The merged commit is always checked before deployment.

Every published article has a Facebook share link and a copy-caption button. Sharing remains the author's choice; there is no automatic social posting or connected Facebook credential. The image-resize tool does not upload local photos; upload a permitted photo as a GitHub attachment and use its public URL as a cover.

## Accessibility and browser regression checks

```sh
npm ci
npx playwright install chromium firefox webkit
npm run test:browser
```

By default browser tests target the live website. Set `SITE_URL=http://127.0.0.1:8000/fieldnotes-journal/` to start and test the local production build. CI runs the suite before deployment and again against the live revision after deployment. Tests use axe for WCAG A/AA rules through 2.2 and best practices, plus keyboard skip navigation, search states, no-JavaScript reading, responsive reflow, enlarged and spaced text, editor drafting, image export, Facebook share metadata and feed/asset availability. A passing automated audit is not a formal accessibility certification or a screen-reader usability study.
