# Artifacto — Lean Implementation Plan

**Artifacto** is a personal knowledge base: AI agent conversations (bug fixes, workarounds, novel solutions) refined into structured blog posts hosted on GitHub Pages.

A **Claude Code SKILL** handles the ingest → refine → draft workflow. The repo contains the Astro site, deploy pipeline, and a standalone image processing script — the minimum code needed for things Claude can't do natively.

---

## Architecture

```
artifacto/
├── site/                        # Astro static site (blog + search + RSS)
│   ├── src/content/blog/        # Published Markdown posts
│   ├── public/images/           # Post images (per-slug directories)
│   └── ...
├── drafts/                      # Staging area for SKILL-generated drafts
├── scripts/
│   └── process-images.py        # Wikimedia search + WebP conversion
├── .claude/skills/
│   └── ingest.md                # SKILL: ingest → refine → draft workflow
├── .github/workflows/
│   └── deploy.yml               # Build Astro + Pagefind → GitHub Pages
├── PLAN.md                      # This file
└── README.md
```

### Workflow

```
User pastes URL/text/MD ──► SKILL reads content ──► SKILL refines into draft ──► User reviews in drafts/
                                                                        │
                                                           Approve: move to site/src/content/blog/
                                                           Reject: delete from drafts/
```

1. **Ingest:** User runs `/ingest` with a URL, file path, or pasted text. The SKILL extracts content, scans existing tags for consistency, and produces a structured blog post draft in `drafts/<slug>.md`.
2. **Review:** The user previews, edits, or rejects the draft.
3. **Publish:** On approval, the SKILL moves the draft to `site/src/content/blog/`, stages a commit, and pushes — triggering GitHub Actions to build and deploy.

### What Code vs SKILL Handles

| Concern | Handled by | Why |
|---|---|---|
| Content extraction (URL/file/text) | **SKILL** | Claude reads URLs and files natively |
| LLM refinement → structured markdown | **SKILL** | This is what a SKILL is — prompt + instructions |
| Tag consistency | **SKILL** | Instructions to read existing posts first |
| Draft lifecycle (save/approve/reject) | **SKILL** | File operations + shell commands |
| Git commit/push | **SKILL** | Shell commands |
| Wikimedia Commons image search | **Python script** | Structured API calls + async HTTP |
| Image → WebP conversion | **Python script** | Pillow processing, deterministic output |
| Site rendering + deploy | **Astro + GH Actions** | Static site + CI/CD |

---

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

Tags are flat, lowercase, hyphenated. No categories. Date field is `pubDate`, collection path is `src/content/blog/`.

---

## Remaining Work

- [ ] **Remove Python backend** — delete `backend/`, `pyproject.toml`, `tests/`
- [ ] **Create SKILL** (`.claude/skills/ingest.md`) — encode refinement prompt, draft workflow, tag scanning, git operations
- [ ] **Extract image script** — move `backend/media/core.py` → `scripts/process-images.py` as a standalone CLI tool
- [ ] **Clean up PLAN.md** — this refactor (done)
- [ ] Configure GitHub Pages source settings (M1.4)
- [ ] Deploy and verify with live post (M1.4 / M5.3)

---

## Design Decisions

| Decision | Rationale |
|---|---|
| SKILL over backend for content pipeline | Personal tool, user has Claude access. A SKILL is the prompt — no need for Python code that writes prompts |
| Keep image processing as Python script | Wikimedia API + Pillow conversion is deterministic work an LLM can't do natively |
| Keep `drafts/` staging area | Human review before publish — don't commit LLM output blindly |
| Keep Astro site full-featured | The site IS the deliverable. Search, RSS, tags, theme — all earn their keep |
