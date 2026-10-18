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
- The contact page uses public GitHub issues; it does not deliver private messages. No invented email address, mailing list, analytics, cookies, or private contact-form backend is configured.
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

## Topic-to-draft AI generation — activation pending

This feature is implemented but no API credential was added during delivery. Paid model calls have not been run or verified. The public studio says generation is inactive until setup is completed.

1. Add an OpenAI API project key as a repository Actions secret named `OPENAI_API_KEY`. Never commit it or enter it in the public website, issue body or chat.
2. Ensure the API project has billing and access to the models in `generation.json`. Defaults are `gpt-5-mini` for article text and `gpt-image-2` for one 1536 × 864 JPEG cover at medium quality. Models and a default limit of three approved-author topic requests per UTC day are configurable in that file. API usage is billed separately; configure provider-side billing controls.
3. Run **Test and publish journal** on `main`. The build exposes only a Boolean setup status in `generation-status.json`; the API credential is never passed to the browser or build scripts.
4. In Author Studio enter a topic, optional angle and source notes, choose a section and tone, then prepare and submit the GitHub generation issue. Requests and generated drafts are public. Only `authors.json` usernames can invoke the AI service.
5. Open the review link returned in the issue comments. It loads the immutable generated draft and cover from a separate `ai-draft-N` branch. Edit the headline, body, image description and Facebook caption. Review notes flag claims to verify. The generator has no web-browsing tool and must not be treated as verified news reporting.
6. Tick the editorial review confirmation and prepare the publication approval. Only the repository owner can submit an accepted approval. Approval commits the reviewed article and its image atomically to `main` and dispatches the existing test/deploy workflow. There is no auto-publication when generation completes, and no Facebook posting from any workflow. After deployment, use the published article’s Facebook share link or copy-caption button.

Generation creates a draft Markdown file outside `content/`, the cover, and a review JSON file on its own branch. It never commits the draft to main. One request makes at most one text call and one image call, with no automatic paid retry. A started-attempt marker and existing-branch check prevent duplicate paid requests from workflow reruns. Create a fresh request after investigating a failure if a second attempt is wanted. Approval requires owner identity, the exact immutable draft reference, and explicit review confirmation; publication receipts prevent duplicated articles and permit deployment re-dispatch after a failed dispatch.

Text uses Responses API JSON-schema output and `store:false`; images use the Images API and JPEG output. That setting does not promise zero provider retention for all services. Documentation: https://developers.openai.com/api/docs/guides/structured-outputs and https://developers.openai.com/api/docs/guides/image-generation . Generated material needs factual, originality and image review; no copyright-clearance guarantee is made.

Backend tests use mocked provider responses and mocked GitHub calls to verify permissions, inactive behavior, rate limits, duplicate protection, draft isolation, API payloads and explicit owner approval. Browser tests use labelled test fixtures for active/review states. No paid AI output was used to claim an end-to-end provider test.
