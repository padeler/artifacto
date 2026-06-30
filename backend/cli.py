"""Artifacto CLI — entry point."""

import typer
import sys
from pathlib import Path
from backend.config import Config
from backend.ingestion.core import ingest_text, ingest_file, ingest_url, handle_images
from backend.refinement.core import refine_content
from backend.tags.index import get_existing_tags
from backend.publishing.drafts import save_draft, get_drafts, get_draft, approve_draft, reject_draft
from backend.publishing.posts import get_posts, delete_post
from backend.media.core import process_image, resolve_suggested_images

import logging

logger = logging.getLogger(__name__)

app = typer.Typer(
    name="artifacto",
    help="Artifacto: AI conversations → structured knowledge base.",
    no_args_is_help=True,
)

@app.command()
def ingest(
    file: Path = typer.Option(None, "--file", "-f", help="Path to markdown or text file"),
    url: str = typer.Option(None, "--url", "-u", help="URL to scrape"),
    text: str = typer.Option(None, "--text", "-t", help="Raw text string"),
    images: list[Path] = typer.Option(None, "--images", "-i", help="Paths to images to attach"),
    pipe: bool = typer.Option(False, "--pipe", "-p", help="Read from stdin")
):
    """Ingest a new artifact and generate a draft."""
    raw_content = ""
    if file:
        raw_content = ingest_file(file)
    elif url:
        import asyncio
        raw_content = asyncio.run(ingest_url(url))
    elif text:
        raw_content = ingest_text(text)
    elif pipe:
        raw_content = ingest_text(sys.stdin.read())
    else:
        typer.echo("Error: Must provide --file, --url, --text, or --pipe", err=True)
        raise typer.Exit(1)
        
    if not raw_content:
        typer.echo("Error: Ingested content is empty.", err=True)
        raise typer.Exit(1)

    existing_tags = get_existing_tags()
    valid_images = []
    if images:
        valid_images = handle_images([str(p) for p in images], slug="temp")
        
    typer.echo("Refining content via LLM...")
    try:
        post = refine_content(raw_content, existing_tags, valid_images)
    except Exception as e:
        typer.echo(f"Refinement failed: {e}", err=True)
        raise typer.Exit(1)
        
    typer.echo(f"Refinement complete. Title: {post.title} (Slug: {post.slug})")
    
    # Save draft
    draft_path = save_draft(post)
    
    # Process images if any
    if valid_images:
        dest_dir = Config.IMAGES_DIR / post.slug
        for img_path in valid_images:
            try:
                process_image(img_path, dest_dir)
            except Exception as e:
                typer.echo(f"Failed to process image {img_path}: {e}", err=True)

    typer.echo(f"\nDraft saved to: {draft_path}")

    # Resolve suggested images from LLM
    if post.suggested_images:
        typer.echo("Sourcing images via Wikimedia Commons...")
        try:
            image_paths = resolve_suggested_images(post.suggested_images, post.slug)
            if image_paths:
                typer.echo(f"Sourced images: {', '.join(image_paths)}")
            else:
                typer.echo("Could not source any matching images.")
        except Exception as e:
            logger.warning(f"Failed to resolve suggested images: {e}")
            typer.echo(f"Warning: Failed to source images ({e})", err=True)

    typer.echo(f"Review and approve with: artifacto approve {post.slug}")

@app.command()
def review(slug: str = typer.Argument(None, help="Slug of the draft to preview")):
    """List pending drafts or preview a specific draft."""
    if slug:
        draft_path = get_draft(slug)
        if not draft_path:
            typer.echo(f"Draft not found: {slug}", err=True)
            raise typer.Exit(1)
        content = draft_path.read_text(encoding="utf-8")
        typer.echo(f"--- DRAFT: {slug} ---")
        typer.echo(content)
        typer.echo("-" * 40)
    else:
        drafts = get_drafts()
        if not drafts:
            typer.echo("No pending drafts.")
            return
        typer.echo("Pending Drafts:")
        for d in drafts:
            typer.echo(f"  - {d.stem}")

@app.command()
def approve(slug: str):
    """Approve a draft and publish it."""
    try:
        dest_path = approve_draft(slug)
        typer.echo(f"Successfully published '{slug}' to {dest_path}")
    except Exception as e:
        typer.echo(f"Failed to approve draft: {e}", err=True)
        raise typer.Exit(1)

@app.command()
def reject(slug: str):
    """Reject a draft and discard it."""
    try:
        reject_draft(slug)
        typer.echo(f"Draft '{slug}' has been rejected and discarded.")
    except Exception as e:
        typer.echo(f"Failed to reject draft: {e}", err=True)
        raise typer.Exit(1)

@app.command("list")
def list_posts():
    """List all published posts."""
    posts = get_posts()
    if not posts:
        typer.echo("No published posts found.")
        return
    typer.echo("Published Posts:")
    for p in posts:
        typer.echo(f"  - {p.stem}")

@app.command()
def delete(slug: str):
    """Delete a published post."""
    typer.confirm(f"Are you sure you want to delete the post '{slug}'?", abort=True)
    try:
        delete_post(slug)
        typer.echo(f"Post '{slug}' deleted successfully.")
    except Exception as e:
        typer.echo(f"Failed to delete post: {e}", err=True)
        raise typer.Exit(1)

@app.command()
def tags():
    """List all existing tags."""
    tags_list = get_existing_tags()
    if not tags_list:
        typer.echo("No tags found.")
        return
    typer.echo("Tags in use:")
    for t in tags_list:
        typer.echo(f"  - {t}")

if __name__ == "__main__":
    app()
