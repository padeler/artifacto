---
title: "Discord Opens Links in Chrome Instead of Firefox on Linux"
summary: "Discord ignores your desktop's default-browser setting and reads xdg-mime directly; on Snap-installed Firefox the desktop file name trips it up, so set the MIME handlers explicitly and fully kill Discord."
pubDate: "2026-06-30"
tags: ["linux", "discord", "firefox", "xdg-mime"]
draft: false
---

Discord on Linux doesn't ask your desktop environment "hey, what's the user's preferred browser?" It skips that entire layer of abstraction and reads the MIME type handlers directly — specifically `x-scheme-handler/http` and `x-scheme-handler/https`. If those point at Chrome, that's where every link lands, regardless of what `xdg-settings` claims your default browser is.

## The fix

Set the MIME handlers explicitly:

```bash
xdg-mime default firefox.desktop x-scheme-handler/http
xdg-mime default firefox.desktop x-scheme-handler/https
```

## Snap Firefox needs a different desktop ID

On Ubuntu, Firefox ships as a Snap by default, and its `.desktop` file isn't named `firefox.desktop` — check with:

```bash
xdg-settings get default-web-browser
# firefox_firefox.desktop
```

That underscore-doubled name is the one Discord is actually probing for. Use it instead:

```bash
xdg-mime default firefox_firefox.desktop x-scheme-handler/http
xdg-mime default firefox_firefox.desktop x-scheme-handler/https
xdg-mime default firefox_firefox.desktop text/html
```

(If you installed Firefox via Flatpak instead, swap in `org.mozilla.firefox.desktop`.)

## Restart Discord for real

Closing the window doesn't cut it — Discord keeps running in the tray. Quit it properly before testing:

```bash
killall Discord
```

Relaunch, click a link, and it should hand off to Firefox like it was supposed to all along.
