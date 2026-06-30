---
title: 'Hello, Artifacto'
summary: "The first post — a knowledge base for the bug fixes, hacks, and 2am breakthroughs that AI pair-programming sessions tend to swallow whole."
pubDate: '2026-06-30'
tags: ['artifacto', 'meta']
draft: false
---

Welcome to **Artifacto** — a living knowledge base for the engineering solutions, dirty workarounds, and occasional flashes of brilliance that surface while pair-programming with an AI agent.

## Why Does This Exist?

Picture it: you're three hours deep in a debugging session, you and your AI agent have tried everything, and then — finally — the test goes green. You feel unstoppable. You close the tab.

The next day you hit the *exact same bug* and have absolutely no memory of how you fixed it. The solution died in a chat log somewhere, alongside every other clever thing you've ever figured out. RIP.

Artifacto exists to stop that bleeding. It:

- **Captures** the raw context — conversations, markdown notes, shared chat links
- **Refines** the mess into a structured, readable post (the LLM does the boring formatting)
- **Publishes** it automatically to this GitHub Pages site

## How It Works

The whole thing runs through a Claude Code SKILL. You point it at some source material and let it cook:

```text
/ingest https://example.com/that-thread-where-i-fixed-it

# ...Claude drafts a post, you review it...

approve my-hard-won-fix
```

Every post goes through a **draft → review → publish** cycle, because letting an LLM publish to your site unsupervised is how you end up explaining things to people.

## What's Next

This site grows one solved problem at a time. Each post is tagged and fully searchable, so when future-you inevitably forgets how to do the thing, the thing will be right here. Stay tuned.
