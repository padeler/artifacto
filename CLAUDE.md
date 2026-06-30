# Artifacto — Project Context

## What It Does

Artifacto is a personal knowledge base: AI agent conversations (bug fixes, workarounds, novel solutions) refined into structured blog posts hosted on GitHub Pages.

Workflow: **Ingest (/ingest SKILL) → Draft (drafts/) → Review → Publish (commit + push)**.

## Architecture

- **Astro site** (`site/`): Static blog with dark theme, Pagefind search, tag browsing, RSS feed. Content lives in `site/src/content/blog/`.
- **SKILL** (`.claude/skills/ingest.md`): Handles content ingestion, LLM refinement, tag scanning, draft lifecycle, git operations.
- **Image script** (`scripts/process-images.py`): Wikimedia Commons search + WebP conversion via Pillow/httpx.

## Content Schema (Front-Matter)

```yaml
---
title: "Post Title"
pubDate: "2026-06-30"
tags: ["tag1", "tag2"]
summary: "One-sentence description."
heroImage: "/images/slug/hero.webp"  # optional
draft: false
---
```

Note: date field is `pubDate`, collection path is `src/content/blog/` (not `posts/`).

## Image Script

```bash
python3 scripts/process-images.py <slug> "search term 1" "search term 2"
```

Searches Wikimedia Commons, downloads matching images as WebP to `site/public/images/<slug>/`. Requires `Pillow` and `httpx`.

## Git

When committing posts, detect the current branch via `git rev-parse --abbrev-ref HEAD`. No hardcoded branch names. Push after commit to trigger deploy.

## Deployment

GitHub Actions (`.github/workflows/deploy.yml`) builds Astro + Pagefind index on push to any tracked branch. Deploy uses `actions/deploy-pages@v4`.
