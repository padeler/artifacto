---
title: "Downgrade VS Code to a Specific Version with Apt"
pubDate: "2026-07-17"
tags: ["linux", "vscode", "apt"]
summary: "A new VS Code release broke your flow? Roll back to any previous version straight from Microsoft's apt repo — and pin it so the next upgrade doesn't undo your work."
heroImage: "../../assets/downgrade-vs-code-to-a-specific-version-with-apt/hero.png"
draft: false
---

Microsoft ships a shiny new VS Code, you `apt upgrade`, and suddenly an extension you rely on throws a fit or the terminal panel starts behaving like it's possessed. You want the old version back. Good news: you don't need to hunt down a `.deb` from the internet's dusty corners — Microsoft's official apt repo keeps a deep history of releases, and `apt` will happily install an older one on top of the newer.

No need to uninstall first. `apt` treats the downgrade as just another version swap.

## 1. Find the exact version string

apt needs the *precise* version string as it appears in the repo — not just `1.121`. List what's available:

```bash
apt list -a code
```

or, equivalently:

```bash
apt-cache madison code
```

You'll get something like:

```text
code/stable 1.121.0-1779186519 amd64
code/stable 1.120.0-1773194512 amd64
```

That trailing number after the dash is a build timestamp, and it's part of the version — you can't omit it.

## 2. Install the version you want

Append `=<version>` to pin the install to an exact release. Copy the full string, dash and timestamp included:

```bash
sudo apt install code=1.121.0-1779186519
```

apt replaces your current install with the older build. Done — except for one trap.

## 3. Lock it, or apt undoes your work

Here's the part everyone forgets. The next time you run `sudo apt upgrade`, apt sees a newer `code` in the repo and cheerfully drags you right back to the version you just escaped. All that effort, gone in one routine update.

Hold the package to freeze it in place:

```bash
sudo apt-mark hold code
```

Now `code` sits out every `apt upgrade` until you say otherwise.

When you're ready to move on — say a patched release fixes whatever sent you running — release the hold:

```bash
sudo apt-mark unhold code
```

## The gist

Three steps: find the version string (`apt list -a code`), install it explicitly (`sudo apt install code=<version>`), and — the step that actually matters — `apt-mark hold code` so your fix survives the next upgrade. The repo remembers old versions so you don't have to.
