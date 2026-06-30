# Artifacto — Project Context

## What It Does

Artifacto is an automated pipeline that transforms ephemeral AI agent conversations (bug fixes, workarounds, novel solutions) into a structured knowledge base hosted on GitHub Pages.

Pipeline: **Ingest → Refine (LLM) → Review (draft) → Publish (commit + push)**.

## Architecture

- **Python backend** (`backend/`): CLI entry point via `typer`, ingestion (scraping/text), LLM refinement, tag indexing, media module (Wikimedia Commons search + WebP conversion), git operations.
- **Astro site** (`site/`): Static blog with dark theme, Pagefind search, tag browsing, RSS feed. Content lives in `site/src/content/blog/`.
- **Drafts** (`drafts/`): Staging area for LLM-generated posts before approval.

## Key Config

- Python dependencies managed via `pyproject.toml` (editable install: `pip install -e .[dev]`).
- Environment variables from project-local `.env` only — `backend/config.py` uses an explicit path to avoid loading parent-dir `.env` files.
- LLM provider set via `LLM_PROVIDER` env var: `claude_code` (default), `anthropic_api`, or `ollama`.
- `ClaudeCodeProvider` tries Anthropic API → Ollama as fallbacks, then produces a heuristic draft if both are unavailable.

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

Note: date field is `pubDate`, collection path is `src/content/blog/` (not `posts/`). This diverges from the original PLAN.md but is consistent across all code.

## Commands

- `artifacto ingest --file|--url|--text|--pipe` — ingest content, produce draft
- `artifacto review [slug]` — list or preview drafts
- `artifacto approve <slug>` — move to blog/, commit, push current branch
- `artifacto reject <slug>` — delete draft + images
- `artifacto list` — show published posts
- `artifacto delete <slug>` — remove published post
- `artifacto tags` — show existing tags

## Git

`commit_and_push` detects the current branch automatically (`git rev-parse --abbrev-ref HEAD`). No hardcoded branch names.

## Tests

```bash
pytest
```

Run from project root. Uses `pytest` framework, tests live in `tests/`.

## Deployment

GitHub Actions (`.github/workflows/deploy.yml`) builds Astro + Pagefind index on push to any tracked branch. Deploy uses `actions/deploy-pages@v4`.
