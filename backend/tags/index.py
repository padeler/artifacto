import re
from pathlib import Path
from backend.config import Config
import logging

logger = logging.getLogger(__name__)

def get_existing_tags() -> list[str]:
    """
    Scan all published posts and drafts to extract the list of existing tags.
    """
    tags = set()
    
    # regex to find tags front-matter: tags: ['tag1', 'tag2'] or tags: [tag1, tag2]
    tags_pattern = re.compile(r"^tags:\s*\[(.*?)\]", re.MULTILINE)
    
    def scan_directory(directory: Path):
        if not directory.exists():
            return
            
        for filepath in directory.glob("**/*.md"):
            try:
                content = filepath.read_text(encoding="utf-8")
                match = tags_pattern.search(content)
                if match:
                    tags_str = match.group(1)
                    # split by comma, remove quotes, strip whitespace
                    extracted_tags = [
                        t.strip().strip("'").strip('"') 
                        for t in tags_str.split(",") if t.strip()
                    ]
                    for t in extracted_tags:
                        if t:
                            tags.add(t)
            except Exception as e:
                logger.warning(f"Failed to scan file for tags {filepath}: {e}")

    scan_directory(Config.POSTS_DIR)
    scan_directory(Config.DRAFTS_DIR)
    
    return sorted(list(tags))
