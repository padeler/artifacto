import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from project-local .env file (don't walk parent dirs)
_env_path = Path(__file__).resolve().parent.parent / ".env"
if _env_path.exists():
    load_dotenv(str(_env_path))

class Config:
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "claude_code")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")
    
    GITHUB_REPO = os.getenv("GITHUB_REPO", "")
    SITE_BASE_URL = os.getenv("SITE_BASE_URL", "")

    # Base directory is the parent of the directory containing this config file (i.e. project root)
    BASE_DIR = Path(__file__).resolve().parent.parent
    SITE_DIR = BASE_DIR / "site"
    POSTS_DIR = SITE_DIR / "src" / "content" / "blog"
    IMAGES_DIR = SITE_DIR / "public" / "images"
    DRAFTS_DIR = BASE_DIR / "drafts"
    LOGS_DIR = BASE_DIR / "logs"

# Ensure essential directories exist
Config.POSTS_DIR.mkdir(parents=True, exist_ok=True)
Config.IMAGES_DIR.mkdir(parents=True, exist_ok=True)
Config.DRAFTS_DIR.mkdir(parents=True, exist_ok=True)
Config.LOGS_DIR.mkdir(parents=True, exist_ok=True)

def setup_logging():
    log_file = Config.LOGS_DIR / "artifacto.log"
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format="[%(asctime)s] [%(levelname)s] [%(module)s] %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S"
    )
    # Also log to console
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] [%(module)s] %(message)s")
    console.setFormatter(formatter)
    logging.getLogger("").addHandler(console)

setup_logging()
