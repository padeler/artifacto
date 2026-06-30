# Artifacto — Project Context

## What It Does

Artifacto is a personal knowledge base: AI agent conversations (bug fixes, workarounds, novel solutions) refined into structured blog posts hosted on GitHub Pages. The goal is to rescue good ideas before they scroll into the void of a closed chat tab.

Workflow: **Ingest (/ingest SKILL) → Draft (drafts/) → Review → Publish (commit + push)**.

## Voice & Tone

The site's mood is **nerdy, funny, engineering, computer science**. When writing site copy, post intros, or summaries, lean into dry developer humor and CS references — self-deprecating debugging stories, playful asides — without sacrificing technical accuracy. Be clever, not cringe; the jokes serve the content, never bury it.

## Architecture

- **Astro site** (`site/`): Static blog with dark theme, Pagefind search, tag browsing, RSS feed. Content lives in `site/src/content/blog/`.
- **SKILL** (`.claude/skills/ingest.md`): Handles content ingestion, LLM refinement, tag scanning, draft lifecycle, git operations.
- **Image script** (`scripts/process-images.py`): Wikimedia Commons search + WebP conversion via Pillow/httpx.

## Content Schema (Front-Matter)

```yaml
---
title: "Post Title"
pubDate: "2026-06-30"
updatedDate: "2026-07-01"          # optional, for republished posts
tags: ["tag1", "tag2"]
summary: "One-sentence description."
heroImage: "../../assets/slug/hero.webp"  # optional; managed asset, relative to the post
draft: false
---
```

Note: date field is `pubDate`, collection path is `src/content/blog/` (not `posts/`). `heroImage` is validated by Astro's `image()` helper, so it must point at a managed asset under `site/src/assets/`, **not** a `/public` URL.

## Image Script

```bash
python3 scripts/process-images.py <slug> "search term 1" "search term 2"
```

Searches Wikimedia Commons, downloads matching images as WebP to `site/src/assets/<slug>/` (managed Astro assets), and prints `heroImage`-ready paths relative to the published post (`../../assets/<slug>/<name>.webp`). Requires `Pillow` and `httpx`.

## Git

When committing posts, detect the current branch via `git rev-parse --abbrev-ref HEAD`. No hardcoded branch names. Push after commit to trigger deploy.

## Deployment

GitHub Actions (`.github/workflows/deploy.yml`) builds Astro + Pagefind index on push to any tracked branch. Deploy uses `actions/deploy-pages@v4`.
