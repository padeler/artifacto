# ingest

Transform raw input (URL, file path, or pasted text) into a structured blog post draft for the Artifacto knowledge base.

## Trigger

The user provides content to be turned into a blog post — via URL, file path, raw text, or stdin paste. 

## Steps

### 1. Ingest the Content

- If **URL**: Fetch and extract meaningful text content. Skip navigation, headers, footers, scripts, styles.
- If **file path**: Read the file contents as text/markdown.
- If **raw text / paste**: Use the text directly.

### 2. Scan Existing Tags

Read existing posts from `site/src/content/blog/` and drafts from `drafts/` to collect all currently used tags. Extract the `tags:` array from each post's YAML front-matter. This gives you a tag vocabulary to reuse.

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
4. If images were provided or should be included, set `heroImage` to the path.
5. **Output ONLY** the raw markdown starting with `---`. No pleasantries, no wrapping in code fences unless that's standard markdown.
6. The blog post should be short, precise and to the point. No one wants to read long pages when looking for a solution

### 4. Save as Draft

Write the output to `drafts/<slug>.md`, where `<slug>` is generated from the title: lowercase, spaces → hyphens, non-alphanumeric removed, trailing hyphens stripped.

- Example: `"Fixing OpenSSL Errors"` → `fixing-openssl-errors.md`
- If a draft with that slug already exists, append `-2`, `-3`, etc.

### 5. Report

Show the user:
- Draft path and file name
- Title and summary from front-matter
- Tags assigned
- A note they can edit the draft before approving

## Operations

After ingesting, the user may ask you to:

### Review Drafts

```bash
# List all drafts with title, date, tags
ls drafts/ && grep -h '^title:\|^pubDate:\|^tags:' drafts/*.md
```

Or show a specific draft:
```bash
cat drafts/<slug>.md
```

### Approve Draft

1. Move the draft from `drafts/<slug>.md` to `site/src/content/blog/<slug>.md`.
2. Stage and commit:
   ```bash
   git add site/src/content/blog/<slug>.md
   git commit -m "feat: publish post <slug>"
   ```
3. Push current branch:
   ```bash
   git push origin $(git rev-parse --abbrev-ref HEAD)
   ```

### Reject Draft

1. Delete `drafts/<slug>.md`.
2. If associated images exist in `site/public/images/<slug>/`, remove them too.
3. Stage deletions and commit:
   ```bash
   git add drafts/ site/public/images/
   git commit -m "chore: reject draft <slug>"
   ```

### Delete Published Post

1. Remove `site/src/content/blog/<slug>.md`.
2. Remove associated images in `site/public/images/<slug>/` if they exist.
3. Stage, commit, push:
   ```bash
   git add site/src/content/blog/ site/public/images/
   git commit -m "chore: delete post <slug>"
   git push origin $(git rev-parse --abbrev-ref HEAD)
   ```

## Image Handling

If the user wants images sourced for a post, run the image processing script:

```bash
python3 scripts/process-images.py <slug> "search term 1" "search term 2"
```

This searches Wikimedia Commons, downloads matching images, converts to WebP, and saves under `site/public/images/<slug>/`. Include the returned paths in the post's front-matter as `heroImage` or inline markdown image links.

## Content Schema

Each post uses this YAML front-matter:

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

Tags are flat, lowercase, hyphenated. Date field is `pubDate`. Collection path is `src/content/blog/` (not `posts/`).
