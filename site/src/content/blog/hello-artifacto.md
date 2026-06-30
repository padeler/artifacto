---
title: 'Hello, Artifacto'
summary: 'The first post on Artifacto — a knowledge base capturing engineering solutions from AI-assisted development sessions.'
pubDate: '2026-06-30'
tags: ['artifacto', 'meta']
draft: false
---

Welcome to **Artifacto** — a living knowledge base that captures the engineering solutions, workarounds, and discoveries that emerge from AI-assisted development sessions.

## Why Artifacto?

When you're pair-programming with an AI agent and you finally crack a tricky bug, the solution often lives and dies in that conversation. Tomorrow, you might hit the same problem and have no easy way to find what worked.

Artifacto solves this by:

- **Capturing** raw context from conversations, markdown notes, or shared chat links
- **Refining** the content with an LLM into a structured, readable technical post
- **Publishing** automatically to this GitHub Pages site

## How It Works

```bash
# Ingest a workaround you just discovered
artifacto ingest --file ./workaround-notes.md

# Review the generated draft
artifacto review

# Approve and publish
artifacto approve my-workaround-post
```

Every post goes through a **draft → review → publish** cycle, so nothing goes live without your approval.

## What's Next

This site will grow as solutions are captured. Each post includes searchable tags and is indexed for full-text search. Stay tuned.
