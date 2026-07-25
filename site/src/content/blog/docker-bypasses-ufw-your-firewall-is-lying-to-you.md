---
title: "Docker Bypasses UFW — Your Firewall Is Lying to You"
summary: "ufw status shows a locked-down server, yet your container on port 8000 answers the whole internet. Docker writes iptables rules ahead of UFW's chain, so UFW never sees the packet."
pubDate: "2026-07-25"
tags: ["docker", "linux", "security", "ufw", "networking"]
heroImage: "../../assets/docker-bypasses-ufw-your-firewall-is-lying-to-you/hero.png"
draft: false
---

You set `default deny incoming`, allowed exactly one port, ran `sudo ufw status verbose`, and admired your fortress. Then you hit your server's public IP on port 8000 from mobile data and your Docker service answers cheerfully.

UFW isn't broken. It just never got the packet.

## Root cause

UFW is a frontend that writes into the `INPUT` chain of `iptables`. Docker writes its own chains into `PREROUTING`/`DOCKER` — which run **first**. A packet for a published container port gets DNAT'd straight into the container before the `INPUT` chain (where all your `ufw` rules live) is ever consulted.

```
Incoming request (port 8000)
        │
        ▼
[ iptables PREROUTING ] ──► port 8000 published? ──► YES ──► forwarded to container
        │                                                   (UFW never consulted)
        ▼
[ ufw-user-input / INPUT ]  ← packet never reaches here
```

This is interface-agnostic. `eth0`, `wlan0`, doesn't matter — deleting UFW rules changes nothing, because none of them are being evaluated.

## Diagnose it

`ufw status` is useless here. Ask the kernel what's actually listening:

```bash
sudo ss -tulpn
```

Read the **Local Address:Port** column:

| Binding | Meaning |
| --- | --- |
| `0.0.0.0:8000` / `[::]:8000` with `docker-proxy` | Exposed to the internet, UFW bypassed |
| `192.168.1.2:8000` with `docker-proxy` | Reachable by anyone on your LAN, UFW bypassed |
| `127.0.0.1:8000` | Actually safe |

If the process is `docker-proxy`, UFW has no say. If it's a native process (`sshd`, `rpcbind`, `slurmd`), UFW still governs it normally.

Also worth a periodic look at the raw truth:

```bash
sudo iptables -L -n -v
```

## Fix A: bind to localhost (do this by default)

If the service sits behind a reverse proxy or is internal, don't publish it to `0.0.0.0`:

```bash
# Exposed to the entire internet
docker run -p 8000:8000 my-app

# Safe: host-local only
docker run -p 127.0.0.1:8000:8000 my-app
```

or in a `docker-compose.yml`:
```yaml
ports:
  - "127.0.0.1:8000:8000"
```

Restart, re-run `sudo ss -tulpn`, confirm it now reads `127.0.0.1:8000`.

## Fix B: ufw-docker (when you want UFW back in charge)

[ufw-docker](https://github.com/chaifeng/ufw-docker) injects rules into the `DOCKER-USER` chain — Docker's official hook for custom firewall rules — so container traffic is evaluated by UFW instead of sailing past it. Container-to-container networking keeps working.

```bash
sudo wget -O /usr/local/bin/ufw-docker https://github.com/chaifeng/ufw-docker/raw/master/ufw-docker
sudo chmod +x /usr/local/bin/ufw-docker
sudo ufw-docker install
sudo ufw reload
```

Then manage container ports through it:

```bash
sudo ufw-docker allow <container> 8000/tcp
sudo ufw-docker allow <container> 8000/tcp from 1.2.3.4
sudo ufw-docker delete allow <container> 8000/tcp
sudo ufw-docker status
```

**The catch:** `systemctl restart docker` can reset Docker's chains. If ports start leaking after a Docker update, re-run `sudo ufw-docker install && sudo ufw reload`.

## It's not just Docker

Anything that hooks `iptables`/`nftables` below UFW's `INPUT` chain does the same trick:

- **Container engines** — Podman (CNI), k3s/k8s CNIs (Flannel, Calico, Cilium), LXD/Incus bridges
- **VPN & overlay networks** — WireGuard/OpenVPN acting as a gateway, Tailscale, ZeroTier (they live in `FORWARD`)
- **VM managers** — libvirt's `virbr0` NAT rules for KVM/QEMU guests
- **Raw `iptables` scripts** — anything an installer added by hand; invisible to `ufw status`, very much active

## The three habits

1. Bind container ports to `127.0.0.1` unless the port genuinely must face the internet.
2. Put public services behind a reverse proxy (Nginx/Traefik/Caddy); expose only 80/443, keep backends on an internal bridge.
3. Make `sudo ss -tulpn` the audit ritual. On a Docker host, `ufw status` is a statement of intent, not a statement of fact.
