---
name: ingest
description: Transform a URL, file path, or pasted text into a structured blog post draft for the Artifacto knowledge base. Use when the user wants to turn raw content (an article, a chat log, notes) into a blog post.
argument-hint: [url-or-file-path]
---

# ingest

Transform raw input (URL, file path, or pasted text) into a structured blog post draft for the Artifacto knowledge base.

## Trigger

The user provides content to be turned into a blog post — via URL, file path, raw text, or stdin paste.

## Arguments

`$ARGUMENTS` (optional): a URL or a file path to ingest.

- If `$ARGUMENTS` is set, treat it as the input source — detect whether it's a URL or a file path (see Step 1) and ingest it directly without asking the user.
- If `$ARGUMENTS` is empty, fall back to whatever content the user pasted or referenced in their message (URL, file path, raw text, or stdin paste).

## Steps

### 1. Ingest the Content

- If **URL**: Fetch and extract meaningful text content. Skip navigation, headers, footers, scripts, styles.
- If **file path**: Read the file contents as text/markdown.
- If **raw text / paste**: Use the text directly.

### 2. Scan Existing Tags

Read existing posts from `site/src/content/blog/` and drafts from `drafts/` to collect all currently used tags. Extract the `tags:` array from each post's YAML front-matter — note tags may be written inline (`tags: ["a", "b"]`) or as a multi-line YAML block list, so parse the front-matter rather than relying on a single-line grep. This gives you a tag vocabulary to reuse.

### 3. Refine into a Blog Post

Act as an elite technical writer and software engineer with a sharp sense of humor. The site's voice is **nerdy, funny, engineering, computer science** — dry developer wit, the occasional CS reference, self-deprecating war stories. Be clever, not cringe: the jokes serve the content and never get in the way of someone trying to find a fix at 2am. Transform the raw input into a polished, structured blog post following these rules:

1. **Extract** the core problem, the actionable solution, and the root cause.
2. **Structure** as Markdown with YAML front-matter starting with `---`.
3. **Front-matter** MUST include:
   - `title`: Concise, descriptive title (string).
   - `summary`: 1-2 sentence description of the issue and fix (string).
   - `pubDate`: Today's date in `YYYY-MM-DD` format (coerced to date by Astro).
   - `tags`: Relevant tags from the existing vocabulary. Only invent new tags if absolutely necessary. Lowercase, hyphenated.
   - `draft`: `false`
   - `updatedDate` (optional): `YYYY-MM-DD`, only when republishing a previously-published post.
4. If images were provided or should be included, set `heroImage` to a path relative to the **published** post location (`site/src/content/blog/<slug>.md`) — e.g. `../../assets/<slug>/hero.webp`. `heroImage` is validated by Astro's `image()` helper, so it must point at a managed asset under `site/src/assets/`, **not** a `/public` URL. See [Image Handling](#image-handling).
5. **Output ONLY** the raw markdown starting with `---`. No pleasantries, no wrapping in code fences unless that's standard markdown.
6. The blog post should be short, precise and to the point. No one wants to read long pages when looking for a solution

### 3.5 Generate Hero Artwork (ComfyUI)

If no images were provided in the source content and no `heroImage` was set, generate fitting artwork via ComfyUI MCP:

1. **Build a prompt** from the post's title, summary, and tags. Prepend an artistic style descriptor matching the site's nerdy-engineering-voice. Keep the final prompt under 60 words.
2. **Generate** via `generate_image` MCP tool:
   ```
   generate_image(prompt=<your_prompt>, width=1024, height=576)
   ```
   This returns immediately with a `prompt_id`.
3. **Wait for completion** — poll `get_job_status(prompt_id=<id>)` until `done` is true (typical ~5-15 seconds).
4. **Download** — call `get_history(prompt_id=<id>)` to obtain the output filename, then `get_image(filename=<name>, save_dir=<local dir>)` to save the PNG locally (works with the remote ComfyUI instance; no `COMFYUI_PATH` needed). Move it to `site/src/assets/<slug>/hero.png` — no format conversion needed, Astro's `image()` helper handles PNG.
5. **Set `heroImage`** in front-matter to `../../assets/<slug>/hero.png`.

If ComfyUI is unreachable or generation fails, log the error and skip — do not block draft creation on missing artwork.

### 4. Save as Draft

Write the output to `drafts/<slug>.md`, where `<slug>` is generated from the title: lowercase, spaces → hyphens, non-alphanumeric removed, trailing hyphens stripped.

- Example: `"Fixing OpenSSL Errors"` → `fixing-openssl-errors.md`
- If a draft with that slug already exists, append `-2`, `-3`, etc.

### 5. Report

Show the user:
- Draft path and file name
- Title and summary from front-matter
- Tags assigned
- Hero image status: generated via ComfyUI, sourced from Wikimedia, or none
- A note they can edit the draft before approving

## Operations

After ingesting, the user may ask you to:

### Approve Draft

1. **Check for a slug collision** with an already-published post. If `site/src/content/blog/<slug>.md` exists, stop and ask the user whether to overwrite or pick a new slug — never silently clobber a published post.
2. Move the draft from `drafts/<slug>.md` to `site/src/content/blog/<slug>.md`.
3. **Validate the build** before pushing — this catches front-matter schema errors (e.g. a broken `heroImage` path) locally instead of in CI:
   ```bash
   cd site && npx astro check
   ```
4. Stage and commit (include images if the post has any):
   ```bash
   git add site/src/content/blog/<slug>.md site/src/assets/<slug>/
   git commit -m "feat: publish post <slug>"
   ```
5. Push current branch:
   ```bash
   git push origin $(git rev-parse --abbrev-ref HEAD)
   ```

### Reject Draft

Drafts in `drafts/` are not tracked in git (only `.gitkeep` is), so rejecting is just a local cleanup — no commit needed.

1. Delete `drafts/<slug>.md`.
2. If associated images exist in `site/src/assets/<slug>/`, remove that directory too.


## Image Handling

### Wikimedia Commons (Primary)

If the user wants images sourced for a post, run the image processing script:

```bash
python3 scripts/process-images.py <slug> "search term 1" "search term 2"
```

This searches Wikimedia Commons, downloads matching images, converts to WebP, and saves them under `site/src/assets/<slug>/` (managed Astro assets, optimized at build time). The script prints paths relative to a published post (`../../assets/<slug>/<name>.webp`) — use those directly as `heroImage` in front-matter or in inline markdown image links. These paths are authored for the post's **published** location under `site/src/content/blog/`, so they only resolve once the draft is approved; that's expected, since `drafts/` is outside the content collection and isn't built.

### ComfyUI Artwork Generation (Fallback)

When no images were provided in the source content and Wikimedia search returns nothing (or wasn't attempted), Step 3.5 generates fitting artwork via ComfyUI MCP using the `generate_image` tool. The prompt is built from the post's title, summary, and tags with an artistic style descriptor matching the site's nerdy-engineering voice. The generated PNG is downloaded via the `get_history` + `get_image` MCP tools and saved as `site/src/assets/<slug>/hero.png` — no format conversion needed. Generation failure is non-blocking — if ComfyUI is unreachable or errors, log and skip.

## Content Schema

Each post uses this YAML front-matter:

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

Tags are flat, lowercase, hyphenated. Date field is `pubDate`. Collection path is `src/content/blog/` (not `posts/`). `heroImage` is validated by Astro's `image()` helper — it must reference a managed asset under `site/src/assets/`, never a `/public` URL.
