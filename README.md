# Fieldnotes ✳

An independent editorial journal for FRYMASTERCHEESE. Separate project; no existing repository is required or modified. Static HTML, responsive CSS, browser-local search, Markdown articles, RSS, sitemap, structured metadata, topic archives, and accessible navigation.

## Run locally

Requires Python 3.12 or newer.

```sh
python -m pip install -r requirements.txt
python build.py
python -m unittest discover -s tests -v
python -m http.server 8000 --directory dist
```

For root-level local preview, temporarily set `url` in `site.json` to `http://localhost:8000`, build, then restore it before committing. The production configuration uses the GitHub Pages project path.

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
- The social image is SVG. Some social platforms will require a PNG or JPEG for image previews; metadata and text previews are provided.
- The site has no paid services or external runtime assets. RSS requires an RSS reader. Search requires JavaScript; topic archives work without it.
- Before using a custom domain, update `site.json`, configure GitHub Pages DNS and HTTPS, and rebuild.

## Verification

Automated checks do not replace a full accessibility audit or testing in every browser. Verify mobile layout, keyboard navigation, search, article URLs, RSS, sitemap, and the deployed commit after significant changes.
