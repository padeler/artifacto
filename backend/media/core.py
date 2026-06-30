import asyncio
import httpx
from pathlib import Path
from PIL import Image
import logging
import urllib.parse
from backend.config import Config

logger = logging.getLogger(__name__)


def resolve_suggested_images(
    suggested_terms: list[str],
    slug: str,
    limit: int = 1,
) -> list[str]:
    """
    Given a list of search terms (from LLM-suggested front-matter),
    search Wikimedia Commons, download the top result for each term,
    process it to WebP, and save under site/public/images/<slug>/.

    Returns a list of relative paths (e.g. ["/images/slug/term.webp"])
    that can be included in the post markdown.
    """
    if not suggested_terms:
        return []

    dest_dir = Config.IMAGES_DIR / slug
    dest_dir.mkdir(parents=True, exist_ok=True)

    downloaded_paths: list[str] = []

    for term in suggested_terms:
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

        # Download the first URL
        tmp_path = dest_dir / f"{term_clean}.tmp"
        try:
            asyncio.run(download_image(urls[0], tmp_path))
        except Exception as e:
            logger.warning(f"Failed to download image for term '{term}': {e}")
            continue

        # Process into WebP
        out_path = process_image(tmp_path, dest_dir, filename_prefix=term_clean)
        tmp_path.unlink(missing_ok=True)

        relative_path = f"/images/{slug}/{out_path.name}"
        downloaded_paths.append(relative_path)
        logger.info(f"Resolved image for term '{term}' -> {relative_path}")

    return downloaded_paths


def process_image(source_path: Path, dest_dir: Path, filename_prefix: str = "") -> Path:
    """
    Process an image: resize if too large, convert to WebP, and save to dest_dir.
    Returns the Path to the new processed image.
    """
    dest_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        with Image.open(source_path) as img:
            # Convert to RGB if it has alpha channel (for better JPEG/WebP compatibility without artifacts)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
                
            # Resize if very large (e.g., max width 1920)
            max_width = 1920
            if img.width > max_width:
                ratio = max_width / img.width
                new_size = (max_width, int(img.height * ratio))
                img = img.resize(new_size, Image.Resampling.LANCZOS)
                
            out_filename = f"{filename_prefix}{source_path.stem}.webp"
            out_path = dest_dir / out_filename
            
            img.save(out_path, "WEBP", quality=85)
            logger.info(f"Processed image and saved to {out_path}")
            return out_path
            
    except Exception as e:
        logger.error(f"Failed to process image {source_path}: {e}")
        raise

async def search_wikimedia_commons(query: str, limit: int = 3) -> list[str]:
    """
    Search Wikimedia Commons for freely licensed images.
    Returns a list of image URLs.
    """
    logger.info(f"Searching Wikimedia Commons for: {query}")
    url = "https://commons.wikimedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "generator": "search",
        "gsrsearch": f"filetype:bitmap|drawing {query}",
        "gsrnamespace": "6", # File namespace
        "gsrlimit": str(limit),
        "prop": "imageinfo",
        "iiprop": "url"
    }
    
    try:
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
    except Exception as e:
        logger.error(f"Failed to search Wikimedia Commons: {e}")
        return []

async def download_image(url: str, dest_path: Path) -> Path:
    """Download an image from a URL to dest_path."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, follow_redirects=True)
            response.raise_for_status()
            
            dest_path.write_bytes(response.content)
            logger.info(f"Downloaded image from {url} to {dest_path}")
            return dest_path
    except Exception as e:
        logger.error(f"Failed to download image from {url}: {e}")
        raise
