import re
import shutil
from pathlib import Path
import logging
from backend.config import Config
from backend.publishing.git import commit_and_push

logger = logging.getLogger(__name__)

POSTS_RE = r"^---\s*\n(.*?)\n---\s*\n(.*)"

def get_posts(tag: str | None = None) -> list[Path]:
    """List all published posts, optionally filtered by tag."""
    if not Config.POSTS_DIR.exists():
        return []
    posts = sorted(list(Config.POSTS_DIR.glob("*.md")))
    if tag is None:
        return posts

    # Filter by tag — scan front-matter for the requested tag
    tags_pattern = re.compile(r"^tags:\s*\[(.*?)\]", re.MULTILINE)
    filtered: list[Path] = []
    for filepath in posts:
        try:
            content = filepath.read_text(encoding="utf-8")
            match = tags_pattern.search(content)
            if not match:
                continue
            tags_str = match.group(1)
            extracted = [
                t.strip().strip("'").strip('"')
                for t in tags_str.split(",")
                if t.strip()
            ]
            if tag in extracted:
                filtered.append(filepath)
        except Exception as e:
            logger.warning(f"Failed to scan post tags {filepath}: {e}")
    return filtered

def delete_post(slug: str) -> None:
    """Delete a published post and its associated images, then commit and push."""
    post_path = Config.POSTS_DIR / f"{slug}.md"
    
    # fallback if slug includes .md
    if not post_path.exists() and slug.endswith(".md"):
        post_path = Config.POSTS_DIR / slug
        slug = post_path.stem
        
    if not post_path.exists():
        raise ValueError(f"Post not found: {slug}")
        
    logger.info(f"Deleting post '{slug}'...")
    
    files_to_commit = [post_path] # git rm will handle it, but wait, `git add` won't remove it.
    
    post_path.unlink()
    
    image_dir = Config.IMAGES_DIR / slug
    if image_dir.exists():
        shutil.rmtree(image_dir)
        files_to_commit.append(image_dir)
        
    # We need to tell git to stage the deletions. `git add --all <paths>` or `git rm`
    # Let's use git add --all which stages deletions too.
    
    repo_dir = Config.BASE_DIR
    from backend.publishing.git import run_git_command, _get_current_branch

    target_branch = _get_current_branch(repo_dir)

    try:
        run_git_command(["add", "--all", str(Config.POSTS_DIR)], cwd=repo_dir)
        run_git_command(["add", "--all", str(Config.IMAGES_DIR)], cwd=repo_dir)

        status = run_git_command(["status", "--porcelain"], cwd=repo_dir)
        if status:
            run_git_command(["commit", "-m", f"chore: delete post {slug}"], cwd=repo_dir)
            run_git_command(["push", "origin", target_branch], cwd=repo_dir)
            logger.info(f"Successfully deleted and pushed changes for '{slug}'.")
    except Exception as e:
        logger.error(f"Failed to commit deletion of post {slug}: {e}")
        raise
