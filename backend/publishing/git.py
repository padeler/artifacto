import subprocess
from pathlib import Path
import logging
from backend.config import Config

logger = logging.getLogger(__name__)

class GitError(Exception):
    pass

def run_git_command(args: list[str], cwd: Path) -> str:
    """Run a git command in the specified directory."""
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        error_msg = f"Git command failed: git {' '.join(args)}\nError: {e.stderr}"
        logger.error(error_msg)
        raise GitError(error_msg)

def _get_current_branch(repo_dir: Path) -> str:
    """Return the name of the current branch."""
    return run_git_command(["rev-parse", "--abbrev-ref", "HEAD"], cwd=repo_dir)


def commit_and_push(files: list[Path], message: str, branch: str | None = None) -> None:
    """
    Stage specified files, commit with the given message, and push to origin.
    If branch is not given, pushes the current branch.
    """
    logger.info(f"Committing and pushing changes: {message}")
    repo_dir = Config.BASE_DIR

    # Add files
    for f in files:
        run_git_command(["add", str(f.resolve())], cwd=repo_dir)

    # Check if there's anything staged
    status = run_git_command(["status", "--porcelain"], cwd=repo_dir)
    if not status:
        logger.info("No changes to commit.")
        return

    # Commit
    run_git_command(["commit", "-m", message], cwd=repo_dir)

    target_branch = branch or _get_current_branch(repo_dir)
    run_git_command(["push", "origin", target_branch], cwd=repo_dir)
    logger.info(f"Successfully pushed changes to origin/{target_branch}.")
