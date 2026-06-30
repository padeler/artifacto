# Artifacto

A personal knowledge base: AI agent conversations (bug fixes, workarounds, novel solutions) refined into structured blog posts, hosted on GitHub Pages.

## How It Works

1. **Ingest**: Use the `/ingest` SKILL with a URL, file path, or pasted text. Claude refines the content into a polished blog post and saves it as a draft in `drafts/`.
2. **Review**: Preview, edit, or reject the draft.
3. **Publish**: Approve the draft — it moves to `site/src/content/blog/`, gets committed and pushed, and GitHub Actions deploys the updated site.

## Architecture

- **Astro Blog** (`site/`): Static blog with dark theme, Pagefind search, tag browsing, RSS feed. Content lives in `site/src/content/blog/`.
- **SKILL** (`.claude/skills/ingest.md`): Handles content ingestion, LLM refinement, tag scanning, draft lifecycle, and git operations.
- **Image Script** (`scripts/process-images.py`): Standalone tool to search Wikimedia Commons, download images, convert to WebP, and save per-post image directories.
- **Drafts** (`drafts/`): Staging area for generated posts before approval.

## Setup

```bash
git clone git@github.com:padeler/artifacto.git
cd artifacto
cd site && npm install && cd ..
```

Optionally, install Python dependencies for the image script:
```bash
pip install Pillow httpx
```

## Usage

### Ingest Content

Use the `/ingest` SKILL. Provide a URL, file path, or paste raw text. Claude will refine it into a structured blog post and save as a draft.

### Review Drafts

Ask to list or view drafts. You can edit them before approving.

### Manage Posts

Ask to approve, reject, or delete posts — the SKILL handles file operations and git commits.

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

Tags are flat, lowercase, and hyphenated. The date field is `pubDate`. Content lives in `src/content/blog/`.

## Local Development

```bash
cd site
npm run dev
```

## Deployment

Push to any tracked branch triggers GitHub Actions: Astro build → Pagefind search index → deploy to GitHub Pages.

## License

MIT
