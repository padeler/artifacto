---
title: "Markdown Preview on Ubuntu: Apostrophe and the MIME Type Fix"
summary: "GNOME Text Editor has no Markdown preview. Install Apostrophe from Flathub, then point text/markdown at it with xdg-mime so double-clicking a .md file stops opening a wall of asterisks."
pubDate: "2026-07-29"
tags: ["linux", "gnome", "flatpak", "xdg-mime", "markdown"]
heroImage: "../../assets/markdown-preview-on-ubuntu-apostrophe-and-the-mime-type-fix/hero.png"
draft: false
---

GNOME Text Editor will happily syntax-highlight your Markdown. It will not render it.

[Apostrophe](https://world.pages.gitlab.gnome.org/apostrophe/) is the native GNOME answer: distraction-free Markdown editing with a live preview on `Ctrl+P`.

## Install

```bash
flatpak install flathub org.gnome.gitlab.somas.Apostrophe
```

## Fix the MIME type

```bash
xdg-mime default org.gnome.gitlab.somas.Apostrophe.desktop text/markdown text/x-markdown
```

Both types matter: `text/markdown` is the modern registration, `text/x-markdown` is the legacy one still emitted by older `shared-mime-info` databases. Register one and you'll hit the other eventually.

