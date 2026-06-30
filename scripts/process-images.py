#!/usr/bin/env python3
"""
Standalone image processing utility for Artifacto blog posts.

Searches Wikimedia Commons for freely licensed images matching provided search terms,
downloads them, converts to WebP, and saves under site/public/images/<slug>/\n\nUsage:
    python scripts/process-images.py <slug> "search term 1" "search term 2"

Example:
    python scripts/process-images.py fixing-openssl "docker network error" "openssl compilation"
"""

import asyncio
import sys
from pathlib import Path
from PIL import Image
import logging
import httpx

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Base directory is the project root (parent of scripts/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
IMAGES_DIR = PROJECT_ROOT / "site" / "public" / "images"


def resolve_suggested_images(slug: str, search_terms: list[str], limit: int = 1) -> list[str]:
    """
    For each search term: query Wikimedia Commons, download the top result,
    convert to WebP, and save under site/public/images/<slug>/.

    Returns a list of relative paths (e.g. ["/images/slug/term.webp"]).
    """
    if not search_terms:
        return []

    dest_dir = IMAGES_DIR / slug
    dest_dir.mkdir(parents=True, exist_ok=True)

    downloaded_paths: list[str] = []

    for term in search_terms:
        term_clean = term.strip().lower().replace(" ", "-")
        if not term_clean:
            continue

        try:
            urls = asyncio.run(search_wikimedia_commons(term_clean, limit=limit))
        except Exception as e:
            logger.warning(f"Failed to search Wikimedia for term '{term}': {e}")
            continue

        if not urls:
            logger.info(f"No Wikimedia results for term '{term_clean}'")
            continue

        tmp_path = dest_dir / f"{term_clean}.tmp"
        try:
            asyncio.run(download_image(urls[0], tmp_path))
        except Exception as e:
            logger.warning(f"Failed to download image for term '{term}': {e}")
            continue

        out_path = process_image(tmp_path, dest_dir, filename_prefix=term_clean)
        tmp_path.unlink(missing_ok=True)

        relative_path = f"/images/{slug}/{out_path.name}"
        downloaded_paths.append(relative_path)
        logger.info(f"Resolved image for term '{term}' -> {relative_path}")

    return downloaded_paths


def process_image(source_path: Path, dest_dir: Path, filename_prefix: str = "") -> Path:
    """Resize if too large, convert to WebP, save to dest_dir."""
    dest_dir.mkdir(parents=True, exist_ok=True)

    with Image.open(source_path) as img:
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        max_width = 1920
        if img.width > max_width:
            ratio = max_width / img.width
            new_size = (max_width, int(img.height * ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)

        out_filename = f"{filename_prefix}{source_path.stem}.webp"
        out_path = dest_dir / out_filename
        img.save(out_path, "WEBP", quality=85)
        logger.info(f"Processed image -> {out_path}")
        return out_path


async def search_wikimedia_commons(query: str, limit: int = 3) -> list[str]:
    """Search Wikimedia Commons for freely licensed images. Returns a list of image URLs."""
    logger.info(f"Searching Wikimedia Commons for: {query}")
    url = "https://commons.wikimedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "generator": "search",
        "gsrsearch": f"filetype:bitmap|drawing {query}",
        "gsrnamespace": "6",
        "gsrlimit": str(limit),
        "prop": "imageinfo",
        "iiprop": "url",
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        pages = data.get("query", {}).get("pages", {})
        urls = []
        for page_id, page_data in pages.items():
            imageinfo = page_data.get("imageinfo", [])
            if imageinfo:
                urls.append(imageinfo[0].get("url"))
        return urls


async def download_image(url: str, dest_path: Path) -> Path:
    """Download an image from a URL to dest_path."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, follow_redirects=True)
        response.raise_for_status()
        dest_path.write_bytes(response.content)
        logger.info(f"Downloaded image from {url} to {dest_path}")
        return dest_path


def main():
    if len(sys.argv) < 3:
        print("Usage: python scripts/process-images.py <slug> \"search term 1\" [\"search term 2\" ...]")
        sys.exit(1)

    slug = sys.argv[1]
    search_terms = sys.argv[2:]

    logger.info(f"Processing images for slug '{slug}' with {len(search_terms)} search term(s)")

    results = resolve_suggested_images(slug, search_terms)

    if results:
        print("\nDownloaded images:")
        for path in results:
            print(f"  {path}")
    else:
        print("No images downloaded (terms may not have matched Wikimedia results).")


if __name__ == "__main__":
    main()
