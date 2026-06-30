import httpx
from bs4 import BeautifulSoup
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class IngestionError(Exception):
    pass

def ingest_text(text: str) -> str:
    """Ingest raw text."""
    logger.info("Ingesting raw text")
    return text.strip()

def ingest_file(file_path: str | Path) -> str:
    """Ingest content from a local file."""
    path = Path(file_path)
    if not path.exists():
        raise IngestionError(f"File not found: {path}")
    
    logger.info(f"Ingesting file: {path}")
    try:
        return path.read_text(encoding="utf-8").strip()
    except Exception as e:
        raise IngestionError(f"Failed to read file {path}: {e}")

async def ingest_url(url: str) -> str:
    """Ingest content from a URL by scraping text and attempting to extract main content."""
    logger.info(f"Ingesting URL: {url}")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Remove scripts, styles, navigation, footer, etc.
            for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
                tag.decompose()
            
            # Attempt to extract text from main content areas, if none found fallback to body
            main_content = soup.find('main') or soup.find('article') or soup.find('body')
            
            if main_content:
                text = main_content.get_text(separator="\n", strip=True)
            else:
                text = soup.get_text(separator="\n", strip=True)
                
            return text
    except Exception as e:
        raise IngestionError(f"Failed to ingest URL {url}: {e}")

def handle_images(image_paths: list[str], slug: str) -> list[Path]:
    """
    Handle provided image paths by returning Path objects.
    Copying images to the site directory is handled during the publish/review phase.
    """
    valid_paths = []
    for ip in image_paths:
        p = Path(ip)
        if p.exists() and p.is_file():
            valid_paths.append(p)
        else:
            logger.warning(f"Image not found or invalid: {p}")
    return valid_paths
