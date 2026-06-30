# Artifacto: Project Bootstrapping & Implementation Plan

**Artifacto** is an automated pipeline designed to bridge the gap between ephemeral AI agent conversations (bug fixes, architectural workarounds, novel solutions) and a permanent, structured, public knowledge base hosted on GitHub Pages (`github.io`).

This document serves as the comprehensive engineering roadmap, technical architecture design, and actionable checklist for building and bootstrapping Artifacto.

---

## 🏗️ Technical Architecture & Workflow

### Monorepo Structure

Everything lives in a single repository (`artifacto`). The repo contains the blog site, the backend processing scripts, the CLI tool, and all configuration.

```
artifacto/
├── site/                        # Astro static site (blog)
│   ├── src/
│   │   ├── content/
│   │   │   └── posts/           # Published Markdown posts
│   │   ├── layouts/
│   │   ├── pages/
│   │   └── components/
│   ├── public/
│   │   └── images/              # Post images / media assets
│   │   │   └── <post-slug>/     # Per-post image directories
│   ├── astro.config.mjs
│   └── package.json
├── backend/                     # Python processing engine
│   ├── ingestion/               # URL scraping, text extraction
│   ├── refinement/              # LLM prompt engineering & orchestration
│   ├── publishing/              # Git commit & push utilities
│   ├── media/                   # Image search, download, generation
│   ├── tags/                    # Tag index management
│   ├── cli.py                   # CLI entry point (typer/click)
│   └── config.py                # Settings & environment management
├── drafts/                      # Review staging area (uncommitted posts)
├── logs/                        # Append-only log files
│   └── artifacto.log
├── tests/                       # Unit & integration tests
├── .github/
│   └── workflows/
│       └── deploy.yml           # GitHub Actions: build & deploy to Pages
├── pyproject.toml               # Python project config
├── PLAN.md                      # This file
└── README.md
```

### System Flow

```
┌─────────────────┐     ┌──────────────────────┐     ┌──────────────┐     ┌──────────────┐
│  1. INGEST      │────►│  2. REFINE (LLM)     │────►│  3. REVIEW   │────►│  4. PUBLISH  │
│                 │     │                      │     │              │     │              │
│ • CLI command   │     │ • Claude Code or     │     │ • Draft saved│     │ • Git commit │
│ • Raw text/MD   │     │   Ollama + Claude    │     │   to drafts/ │     │ • Push to    │
│ • URL scraping  │     │ • Content structuring│     │ • User edits │     │   main branch│
│ • Image attach  │     │ • Image sourcing     │     │ • User       │     │ • GH Actions │
│                 │     │ • Tag assignment      │     │   approves   │     │   deploys    │
└─────────────────┘     └──────────────────────┘     └──────────────┘     └──────────────┘
```

1. **Trigger:** The engineer runs a CLI command with a raw context payload (text, `.md` file, URL, or images).
2. **Ingestion & Extraction:** The backend ingests the data. If given a URL, it scrapes and extracts the conversation cleanly.
3. **Refinement (The Agent Worker):** The text is processed by an LLM (Claude via subscription, or Ollama + local model). The model refines content into a structured blog post, assigns tags (reusing existing ones where appropriate), and sources/generates relevant images.
4. **Review:** The generated Markdown post is saved as a **draft** in `drafts/`. The user can preview, edit, or reject it before publishing.
5. **Publishing:** Upon approval, the draft is moved to `site/src/content/posts/`, committed, and pushed. GitHub Actions builds and deploys to GitHub Pages.

### LLM Provider Strategy

The LLM is configurable. Two supported modes:

- **Claude Code (primary):** Claude Code acts as the harness — the CLI delegates to Claude Code which handles refinement, image sourcing, and tag management directly.
- **Ollama + Claude API:** For automated/headless usage, the backend can call Ollama for local inference or the Anthropic API directly.

Configuration is managed via environment variables and/or a `.env` file.

---

## 🗺️ Project Milestones Overview

* **Milestone 1: Monorepo Setup & Local Blog** (Foundation)
* **Milestone 2: Core Processing Engine (Ingestion & LLM Refinement)** (Brain)
* **Milestone 3: Review Workflow & Publishing Pipeline** (Pipeline)
* **Milestone 4: CLI & Media Handling** (Frictionless Input)
* **Milestone 5: Search, Polish, & Launch** (Hardening)

---

## 📝 Detailed Checklist

### Milestone 1: Monorepo Setup & Local Blog
*Goal: Establish the monorepo structure, initialize Astro, and get a working local blog with GitHub Pages deployment.*

- [x] **1.1. Initialize Monorepo Structure**
  - [x] Create the directory layout as defined in the architecture section above.
  - [x] Initialize `pyproject.toml` for the Python backend (use `uv` or `poetry`).
  - [x] Create a `.env.example` file documenting all required environment variables.

- [x] **1.2. Initialize Astro Blog**
  - [x] Initialize an **Astro** project inside `site/` using `npm create astro@latest`.
  - [x] Choose or build a minimal, clean, developer-centric technical blog theme.
  - [x] Ensure support for syntax highlighting (Shiki) for code snippets.
  - [x] Configure `astro.config.mjs` with the correct `site` and `base` for GitHub Pages deployment.

- [x] **1.3. Define Content Schema (Front-Matter)**
  - [x] Define the Markdown front-matter fields for posts:
    ```yaml
    ---
    title: "Fixing OpenSSL Compilation Errors in Node v18"
    date: 2026-06-30
    tags: ["nodejs", "openssl", "docker"]
    summary: "Brief description of the fix for quick preview lists."
    heroImage: "/images/fixing-openssl/hero.webp"  # optional
    draft: false
    ---
    ```
  - [x] No `category` field — only `tags`. Tags are flat, lowercase, hyphenated.
  - **Note:** Content collection lives at `src/content/blog/` (not `posts/`). Date field is `pubDate` (not `date`). This is consistent across all code.

- [x] **1.4. Configure GitHub Pages Deployment**
  - [x] Create `.github/workflows/deploy.yml` using the official `withastro/action`.
  - [ ] Configure the GitHub repo settings to use "GitHub Actions" as the Pages source.
  - [ ] Test with a dummy `hello-world.md` post to verify the live URL works.

---

### Milestone 2: Core Processing Engine (Ingestion & LLM Refinement)
*Goal: Build the Python backend that ingests raw input and uses an LLM to transform it into clean, structured Markdown with images and tags.*

- [x] **2.1. Environment & Configuration**
  - [x] Set up Python project with dependencies: `typer`, `httpx`, `beautifulsoup4`, `python-dotenv`.
  - [x] Create `backend/config.py` to manage settings from `.env`:
    - `LLM_PROVIDER` (claude_code | anthropic_api | ollama)
    - `ANTHROPIC_API_KEY` (optional, for direct API usage)
    - `OLLAMA_MODEL` (optional, for Ollama usage)
    - `GITHUB_REPO` (owner/repo)
    - `SITE_BASE_URL`
  - [x] Set up file-based logging to `logs/artifacto.log` (append mode, timestamped entries).

- [x] **2.2. Build Ingestion Module**
  - [x] Implement text/markdown ingestion (accept raw strings or file paths).
  - [x] Implement URL scraping using `httpx` + `beautifulsoup4`:
    - Strip UI elements and extract conversation message blocks.
    - Handle common conversation-sharing URL formats.
  - [ ] Implement image attachment handling:
    - [x] Accept image file paths alongside text input.
    - [ ] Copy provided images to the appropriate `site/public/images/<post-slug>/` directory.

- [x] **2.3. Build Tag Index Manager**
  - [x] Implement `backend/tags/index.py`:
    - [x] Scan all published posts in `site/src/content/blog/` and `drafts/` to build a tag index.
    - [x] Expose a function `get_existing_tags() -> list[str]` that returns all currently used tags.
    - [x] The LLM prompt includes this tag list so the agent can reuse existing tags or create new ones only when necessary.

- [x] **2.4. Engineer the LLM Refinement Prompt**
  - [x] Formulate a strict **System Prompt** for the LLM. It must instruct the model to:
    - [x] Act as an elite technical writer.
    - [x] Extract the clear **Problem Statement**, the **Actionable Solution**, and the underlying **Root Cause**.
    - [x] Structure the final output strictly as Markdown with the required front-matter header block.
    - [x] Assign tags from the provided existing tag list where applicable; create new tags sparingly.
    - [x] Suppress conversational fluff ("Sure, here is the blog post...").
  - [x] Provide the existing tag list as context in the prompt.

- [x] **2.5. Integrate LLM Client**
  - [x] Implement a provider-agnostic interface:
    ```python
    class LLMProvider(Protocol):
        def refine(self, raw_text: str, existing_tags: list[str], images: list[Path]) -> RefinedPost: ...
    ```
  - [x] Implement providers:
    - [x] `ClaudeCodeProvider` — tries Anthropic API / Ollama as fallbacks; produces heuristic draft if all fail.
    - [x] `AnthropicAPIProvider` — direct API calls using the `anthropic` SDK.
    - [x] `OllamaProvider` — local inference via Ollama REST API.
  - [x] `RefinedPost` dataclass containing: `title`, `slug`, `tags`, `summary`, `markdown_body`, `suggested_images`.

- [x] **2.6. Build Media Module**
  - [x] Implement `backend/media/`:
    - [x] **Image search:** Given a post topic, search for relevant Creative Commons / freely licensed images (via Wikimedia Commons API).
    - [ ] **Image generation:** Optionally generate images using an image generation API (if configured).
    - [x] **Image processing:** Download, resize, and convert images to WebP for performance.
    - [x] Save images to `site/public/images/<post-slug>/`.
    - [x] Return image paths for inclusion in the post markdown.

---

### Milestone 3: Review Workflow & Publishing Pipeline
*Goal: Implement the draft-review-publish cycle and content management (including deletion).*

- [x] **3.1. Implement Draft Workflow**
  - [x] After LLM refinement, save the generated post to `drafts/<slug>.md`.
  - [x] Save associated images to `site/public/images/<slug>/` (images are pre-staged).
  - [x] Display the draft path and a preview summary in CLI output.
  - [x] Support the following review actions via CLI:
    - [x] `artifacto review` — list all pending drafts.
    - [x] `artifacto review <slug>` — display a specific draft for review.
    - [x] `artifacto approve <slug>` — move draft to `site/src/content/blog/`, commit, and push.
    - [x] `artifacto reject <slug>` — delete the draft and its staged images.
  - [x] The user can also manually edit the draft file before approving.

- [x] **3.2. Implement Publishing**
  - [x] Move approved draft from `drafts/` to `site/src/content/blog/`.
  - [x] Auto-generate a clean file slug from the title (e.g., `fixing-openssl-compilation-errors.md`).
  - [x] Commit all changes (post + images) with a descriptive commit message.
  - [x] Push to the current branch, triggering the GitHub Actions deployment.

- [x] **3.3. Implement Content Deletion**
  - [x] `artifacto delete <slug>` — removes a published post:
    - [x] Delete the post file from `site/src/content/blog/`.
    - [x] Delete the associated image directory from `site/public/images/<slug>/`.
    - [x] Commit with a message like `"chore: delete post <slug>"`.
    - [x] Push to trigger redeployment.
  - [x] `artifacto list` — list all published posts with their slugs, titles, dates, and tags.

- [ ] **3.4. Deduplication**
  - [ ] Before saving a draft, compute a content fingerprint (e.g., hash of the source input text).
  - [x] Check against existing posts and drafts by slug. Warn the user if a similar post already exists.
  - [ ] Allow the user to force-proceed if desired.

- [x] **3.5. Logging**
  - [x] All operations (ingest, refine, approve, reject, delete) are logged to `logs/artifacto.log`.
  - [x] Log format: `[ISO-TIMESTAMP] [LEVEL] [ACTION] message`.
  - [x] CLI output provides real-time feedback for all operations.

---

### Milestone 4: CLI Interface & Media Handling
*Goal: Build a polished CLI tool that makes logging an artifact frictionless.*

- [x] **4.1. Build the Artifacto CLI Tool**
  - [x] Create the CLI using `typer` with the following commands:
    ```bash
    # Ingest from a file
    artifacto ingest --file ./workaround-notes.md

    # Ingest from a URL
    artifacto ingest --url "https://shared-chat-link.com/xyz"

    # Ingest with attached images
    artifacto ingest --file ./notes.md --images ./screenshot1.png ./diagram.svg

    # Pipe clipboard content
    xclip -o | artifacto ingest --pipe

    # Review drafts
    artifacto review
    artifacto review fixing-openssl

    # Approve / reject drafts
    artifacto approve fixing-openssl
    artifacto reject fixing-openssl

    # Manage published posts
    artifacto list
    artifacto list --tag nodejs
    artifacto delete fixing-openssl

    # Show existing tags
    artifacto tags
    ```
  - [x] Package with `pyproject.toml` entry points so it installs via `pip install -e .`.
  - [x] All CLI output includes clear status messages and errors. No silent failures.
  - **Note:** `artifacto list --tag nodejs` is not yet implemented (no `--tag` filter flag in the CLI).

- [ ] **4.2. Image Handling in the Pipeline**
  - [ ] User-provided images: Copy to `site/public/images/<slug>/`, update markdown references.
  - [ ] Agent-sourced images: The LLM suggests image search terms → media module finds/downloads images.
  - [ ] Agent-generated images: If configured, generate diagrams or illustrations via image generation API.
  - [ ] All images are converted to WebP, optimized, and referenced with relative paths in the post.

---

### Milestone 5: Search, Polish, & Launch
*Goal: Add client-side search, finalize testing, and prepare for daily use.*

- [ ] **5.1. Integrate Pagefind for Client-Side Search**
  - [x] Install and configure [Pagefind](https://pagefind.app/) as a post-build step in the Astro site (deploy.yml includes `npx pagefind --site dist`).
  - [ ] Pagefind runs after `astro build`, indexes all content, and produces a static search index.
  - [x] Add a search UI component to the blog (dedicated search page at `/search`).
  - [ ] Ensure tags are indexed and searchable — users can search by tag name.
  - [ ] Verify search works correctly on GitHub Pages (all assets load from correct paths).

- [x] **5.2. Tag Browsing**
  - [x] Create a `/tags` page on the blog listing all tags with post counts.
  - [x] Create per-tag pages (`/tags/<tag>`) listing all posts with that tag.
  - [ ] Integrate tag links into post layouts (clickable tags in post headers/footers).

- [ ] **5.3. Testing**
  - [ ] **Unit tests** for:
    - [x] Ingestion module (text extraction, URL parsing).
    - [ ] Tag index manager (scanning, deduplication).
    - [ ] Slug generation and sanitization.
    - [ ] Content fingerprinting / deduplication logic.
  - [ ] **Integration tests** for:
    - [ ] Full ingest → refine → draft flow (using a mock LLM provider).
    - [ ] Draft → approve → publish flow (using a local git repo).
    - [ ] Draft → reject flow.
    - [ ] Delete flow.
  - [ ] **E2E test:**
    - [ ] Run the full pipeline with a test payload and verify the Astro site builds successfully.
  - [x] Use `pytest` as the test framework.

- [ ] **5.4. Documentation**
  - [ ] Complete `README.md` with:
    - [x] Project overview and architecture diagram.
    - [ ] Installation instructions (Python + Node.js dependencies).
    - [ ] Configuration guide (`.env` setup, LLM provider selection).
    - [ ] CLI usage examples.
    - [ ] Contribution guidelines.
  - [ ] Document LLM prompt tuning patterns so the blog's "voice" can be adjusted over time.

- [ ] **5.5. Graceful Error Handling**
  - [x] Implement fallback parsing if the LLM breaks the front-matter YAML structure (heuristic draft mode).
  - [ ] Add YAML validation for front-matter (must start/end with `---`, valid YAML between).
  - [x] Handle network errors (LLM timeouts, git push failures) with clear CLI messages and log entries.

---

## 🚀 Execution Strategy

1. **Phase 1 (Done):** Milestones 1-3 are structurally complete. The Astro blog is built with a custom theme, the full backend pipeline (ingest → refine → draft → approve/reject) is implemented, and the CLI covers all core commands.
2. **Remaining Work:**
   - Initial commit + push to test the deploy workflow (M1.4)
   - End-to-end integration test: run `artifacto ingest` with real input, verify a draft is produced and can be approved
   - Content fingerprinting deduplication (M3.4) — currently only checks slug collision
   - Image generation via API (M2.6) — not yet implemented
   - User-provided image integration on publish (M4.2) — updating markdown references with final WebP paths
   - `artifacto list --tag` filter (M4.1)
   - Unit/integration test coverage (M5.3)
   - README completion (M5.4)

## 🔧 Fixes Applied (2026-06-30)

| # | Issue | Fix |
|---|-------|-----|
| 1 | `backend/refinement/providers.py` had duplicate `import re as regex` + unreferenced name `regex` in slug generation | Removed duplicate import, replaced `regex.sub()` with `re.sub()` |
| 2 | `ClaudeCodeProvider.refine()` raised `NotImplementedError`, crashing the default ingest flow | Implemented fallback chain: tries Anthropic API → Ollama → heuristic draft (extracts first heading as title, passes raw text as body) |
| 3 | `commit_and_push` and `delete_post` hardcoded pushing to `main` branch | Both now detect current branch via `git rev-parse --abbrev-ref HEAD`; `commit_and_push` accepts optional `branch` param |
| 4 | `.gitignore` existed but was untracked | Added to the initial commit |
| 5 | `load_dotenv()` walked parent directories and tried to parse `~/.env`, producing warnings on import | `config.py` now loads only project-local `.env` with explicit path |