---
title: "Self-Hosting ComfyUI as an MCP Server with Docker"
summary: "Deploy ComfyUI in Docker with MCP integration for local AI image generation accessible from Claude Code and other MCP clients, secured with token auth and IP allowlisting."
pubDate: "2026-07-07"
tags: ["docker", "comfyui", "ai", "self-hosted", "mcp"]
heroImage: "../../assets/image-gen-mcp/hero.png"
draft: false
---

[image_gen_mcp](https://github.com/padeler/image_gen_mcp) packages ComfyUI, the comfyui-MCP server, and Nginx into Docker Compose with built-in security—giving you local image generation without cloud API costs or rate limits.

## Setup

```bash
git clone https://github.com/padeler/image_gen_mcp
cd image_gen_mcp
docker-compose up -d
./scripts/download_models.sh
```

Configure `.env` with auth token, GPU settings, and IP allowlist.

## What You Get

- **Text-to-image, image-to-image** via SDXL
- **Video generation** (LTX-2.3)
- **Audio synthesis** (ACE Step 1.5, Stable Audio 3)
- **ControlNet, IP-Adapter, background removal**
- **Workflow management** and custom nodes
- **MCP access** from Claude Code, Claude Desktop, Cursor

## Security

1. Bearer token authentication
2. Source-IP allowlist
3. Bind-IP configuration for multi-homed systems

## Requirements

- Docker + NVIDIA Container Toolkit
- NVIDIA GPU (CUDA 13.0 is the default, comfyUI images for other CUDA versions are also available) 
- GPU with enough VRAM
