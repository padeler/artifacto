import shutil
from pathlib import Path
import logging
from backend.config import Config
from backend.refinement.providers import RefinedPost
from backend.publishing.git import commit_and_push

logger = logging.getLogger(__name__)

def save_draft(post: RefinedPost) -> Path:
    """Save a refined post as a draft."""
    draft_path = Config.DRAFTS_DIR / f"{post.slug}.md"

    draft_path.write_text(post.markdown_body, encoding="utf-8")
    logger.info(f"Saved draft to {draft_path}")
    return draft_path

def get_drafts() -> list[Path]:
    """List all pending drafts."""
    if not Config.DRAFTS_DIR.exists():
        return []
    return sorted(list(Config.DRAFTS_DIR.glob("*.md")))

def get_draft(slug: str) -> Path | None:
    """Get a specific draft by slug."""
    draft_path = Config.DRAFTS_DIR / f"{slug}.md"
    if draft_path.exists():
        return draft_path
    
    # fallback to trying without .md in case it was provided with extension
    if slug.endswith(".md"):
        draft_path = Config.DRAFTS_DIR / slug
        if draft_path.exists():
            return draft_path
            
    return None

def approve_draft(slug: str) -> Path:
    """Approve a draft: move to posts, commit, and push."""
    draft_path = get_draft(slug)
    if not draft_path:
        raise ValueError(f"Draft not found: {slug}")
        
    post_slug = draft_path.stem
    dest_path = Config.POSTS_DIR / draft_path.name
    
    logger.info(f"Approving draft '{post_slug}'...")
    
    # Move file
    shutil.move(str(draft_path), str(dest_path))
    
    # We should also handle images, assuming they are in public/images/slug/
    # If they were pre-staged, they are already there. We just need to commit them.
    image_dir = Config.IMAGES_DIR / post_slug
    files_to_commit = [dest_path]
    if image_dir.exists():
        files_to_commit.append(image_dir)
        
    # Commit and push
    commit_and_push(
        files=files_to_commit,
        message=f"feat: publish post {post_slug}"
    )
    
    return dest_path

def reject_draft(slug: str) -> None:
    """Reject a draft: delete the file and any pre-staged images."""
    draft_path = get_draft(slug)
    if not draft_path:
        raise ValueError(f"Draft not found: {slug}")
        
    post_slug = draft_path.stem
    
    logger.info(f"Rejecting draft '{post_slug}'...")
    draft_path.unlink()
    
    image_dir = Config.IMAGES_DIR / post_slug
    if image_dir.exists():
        shutil.rmtree(image_dir)
        logger.info(f"Removed staged images for '{post_slug}'")
