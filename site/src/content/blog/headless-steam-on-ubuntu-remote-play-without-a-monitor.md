---
title: "Headless Steam on Ubuntu: Remote Play Without a Monitor"
summary: "Stream games from a monitorless Ubuntu + NVIDIA box to a Steam Link: fake a monitor with ConnectedMonitor + a custom EDID, pin X to one GPU, and give Steam its own PulseAudio daemon with a null sink so audio actually arrives."
pubDate: "2026-10-01"
tags: ["linux", "nvidia", "steam", "xorg", "audio"]
heroImage: "../../assets/headless-steam-on-ubuntu-remote-play-without-a-monitor/hero.png"
draft: false
---

The gaming box lives in a closet. It has an NVIDIA GPU and zero monitors. Steam Remote Play needs a real framebuffer, NVIDIA won't make one without a display, and a $5 HDMI dummy plug is a hardware fix for a software problem. So we lie to the driver instead.

**Target:** Ubuntu 24.04, NVIDIA driver 580, Xorg, Openbox, Steam from multiverse.

## How it works

- Xorg runs on `:0`. The NVIDIA driver is told a monitor is connected (`ConnectedMonitor`) and handed a fake EDID (`CustomEDID`).
- `AutoAddGPU false` keeps the second GPU out of X, so it stays free for CUDA.
- Steam gets its **own** PulseAudio daemon with a null sink (`steam_sink`) to capture.
- Openbox is there because Steam refuses to live without a window manager.

## 1. Packages

```bash
sudo apt install nvidia-driver-580   # or whatever `ubuntu-drivers list` recommends; reboot
sudo add-apt-repository -y multiverse
sudo dpkg --add-architecture i386
sudo apt update
sudo apt install -y xserver-xorg-core x11-xserver-utils openbox dbus-x11 \
  pulseaudio pulseaudio-utils steam-installer
```

Keep `pipewire-pulse` installed. We're not replacing it, just going around it.

## 2. Find the GPU's BusID (multi-GPU)

`nvidia-smi` prints hex. Xorg wants decimal, because of course it does:

```bash
nvidia-smi --query-gpu=name,pci.bus_id --format=csv,noheader | \
while IFS=', ' read -r name busid; do
  IFS=':.' read -r _ bus dev fn <<<"$busid"
  printf '%-30s PCI:%d:%d:%d\n' "$name" "0x$bus" "0x$dev" "0x$fn"
done
# 00000000:0B:00.0 → PCI:11:0:0
```

For the connector, `DP-0` exists on most modern cards. After X has started once, `grep -E 'DFP-[0-9]+' /var/log/Xorg.0.log` lists the real ones. (`DP-0` and `DFP-1` may be the same port under two names. Both work.)

## 3. Fake EDID

Any monitor's EDID works. You can copy one from `/sys/class/drm/card*-DP-*/edid`, or use this reference one. It's named `1080p.bin`, but it's actually a Dell S2725DS whose native mode is 1440p. Naming things is one of the two hard problems.

```bash
sudo mkdir -p /usr/lib/firmware/edid
base64 -d <<'EOF' | sudo tee /usr/lib/firmware/edid/1080p.bin >/dev/null
AP///////wAQrH7RTDAzMS4iAQOAPCJ46hRlqlNOnyQPUFSlSwBxT4FAgYCBwIEAlQCzANHAVl4A
oKCgKVAwIDUAVVAhAAAaAAAA/wA3UFQ5UzQ0CiAgICAgAAAA/ABERUxMIFMyNzI1RFMKAAAA/QAw
ZByXPAAKICAgICAgAQoCAyvxSwMCEhEBEwQUHwUQIwkHB4MBAABnAwwAEAA4RGrYXcQBeIgAADBk
AjqAGHE4LUBYLEUAVVAhAAAefjkAoIA4H0AwIDoAVVAhAAAaWqAAoKCgRlAwIDUAVVAhAAAaAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAEA==
EOF
sha256sum /usr/lib/firmware/edid/1080p.bin
# 9f1481783ae1f457aba3dfe71e7f78cf9da365036c31e7cb4cc0062f9db1e67d
```

## 4. Xorg config

`/etc/X11/xorg.conf.d/10-headless-nvidia.conf`. Adjust `BusID`, the connector (all three options), and `Virtual`, which must be a mode the EDID supports:

```
Section "ServerFlags"
    Option      "AutoAddGPU" "false"      # keep other GPUs out of X
EndSection

Section "Device"
    Identifier  "NvidiaGPU"
    Driver      "nvidia"
    BusID       "PCI:11:0:0"
    Option      "AllowEmptyInitialConfiguration" "true"
    Option      "ConnectedMonitor" "DP-0"
    Option      "UseDisplayDevice" "DP-0"
    Option      "CustomEDID" "DP-0:/usr/lib/firmware/edid/1080p.bin"
EndSection

Section "Screen"
    Identifier "Screen0"
    Device     "NvidiaGPU"
    DefaultDepth 24
    SubSection "Display"
        Depth   24
        Virtual 1920 1080
    EndSubSection
EndSection
```

Single GPU? Drop `BusID` and `ServerFlags`. Games render on whichever GPU runs the X screen.

## 5. Start X

```bash
sudo -v && sudo Xorg :0 -noreset -logfile /var/log/Xorg.0.log &
```

`-noreset` keeps X alive when Steam disconnects. Running `sudo -v` first stops sudo from prompting for a password in the background, where you'd never see it.

## 6. Start Steam (the audio part is the actual fix)

The audio took the longest. Symptom: no sound on the Steam Link, plus stream freezes and display glitches. The exact root cause was never pinned down. A separate PulseAudio daemon that only Steam uses fixed it, and that's what this script does:

```bash
#!/usr/bin/env bash
set -euo pipefail
export DISPLAY=":0"
# Don't touch this line: it hides the desktop's PipeWire socket, forcing a private pulseaudio
export XDG_RUNTIME_DIR="/tmp/xdg-runtime-$USER"
mkdir -p "$XDG_RUNTIME_DIR" && chmod 700 "$XDG_RUNTIME_DIR"

[[ -z "${DBUS_SESSION_BUS_ADDRESS:-}" ]] && eval "$(dbus-launch --sh-syntax)"

pactl info >/dev/null 2>&1 || pulseaudio --start --exit-idle-time=-1
pactl list short sinks | awk '{print $2}' | grep -qx steam_sink || \
  pactl load-module module-null-sink sink_name=steam_sink sink_properties=device.description=SteamSink >/dev/null
pactl set-default-sink steam_sink || true

xset s off || true; xset s noblank || true; xset -dpms || true

pgrep -u "$USER" -x openbox >/dev/null || { openbox >openbox.log 2>&1 & sleep 1; }

if ! pgrep -u "$USER" -f "(/|^)steam($| )" >/dev/null; then
  PULSE_LATENCY_MSEC=60 STEAM_RUNTIME=1 steam -no-cef-sandbox >steam.log 2>&1 &
fi
```

- `XDG_RUNTIME_DIR` in `/tmp` means `pactl` can't find PipeWire at `/run/user/$UID/pulse/native`, so the script starts a private `pulseaudio` that only Steam talks to.
- `--exit-idle-time=-1` keeps the daemon running between songs.
- `PULSE_LATENCY_MSEC=60` stops the audio from crackling.
- `-no-cef-sandbox` stops Steam's web helper from crashing.
- **Order matters:** start the daemon and sink *before* Steam. If you fix audio while Steam is running, restart Steam.

To stop: `pkill -u "$USER" -f "(/|^)steam($| )"; pkill -u "$USER" -f steamwebhelper; pulseaudio -k`.

## 7. First login and Remote Play

- Logging in the first time needs eyes on the screen. Either pair a Steam Link, or use VNC temporarily: `x11vnc -display :0 -localhost` + `ssh -L 5900:localhost:5900 <host>`.
- Enable **Settings → Remote Play**, enter the PIN on the Link, and set the streaming resolution to match `Virtual`.
- On `ufw`: `sudo ufw allow 27031:27036/udp && sudo ufw allow 27036:27037/tcp`.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `cannot open display :0` | X isn't running. Check `/var/log/Xorg.0.log` for `(EE)` |
| `(EE) No devices detected` | Wrong `BusID`. It must be decimal |
| Black screen / wrong resolution | Bad connector name, or `Virtual` isn't an EDID mode |
| X also shows up on the second GPU | Add `AutoAddGPU false` |
| No sound, stream freezes | Steam is on PipeWire, not `steam_sink`. Check `pactl info` with the `/tmp` `XDG_RUNTIME_DIR`, then restart Steam |
| Steam window missing or unfocusable | Openbox isn't running |
| `Unable to find a valid menu file` | Openbox complaining. Ignore it |
