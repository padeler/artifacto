"""Integration tests for draft workflow (approve/reject) with mocked git."""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestDraftWorkflow:
    """Test draft save, approve, reject flows with mocked git operations."""

    @pytest.fixture
    def dirs(self, tmp_path):
        """Create temporary directory structure mimicking the project."""
        drafts_dir = tmp_path / "drafts"
        posts_dir = tmp_path / "site" / "src" / "content" / "blog"
        images_dir = tmp_path / "site" / "public" / "images"
        repo_dir = tmp_path

        drafts_dir.mkdir(parents=True)
        posts_dir.mkdir(parents=True)
        images_dir.mkdir(parents=True)

        return {
            "drafts": drafts_dir,
            "posts": posts_dir,
            "images": images_dir,
            "repo": repo_dir,
        }

    def _make_refined_post(self, title="Test Post", slug="test-post", tags=None):
        from backend.refinement.providers import RefinedPost
        return RefinedPost(
            title=title,
            slug=slug,
            tags=tags or ["test"],
            summary="A test post.",
            markdown_body="---\ntitle: Test Post\n---\n# Content",
            suggested_images=[],
        )

    def test_save_and_get_draft(self, dirs):
        from backend.publishing.drafts import save_draft, get_drafts, get_draft

        with patch("backend.publishing.drafts.Config") as mock_config:
            mock_config.DRAFTS_DIR = dirs["drafts"]
            mock_config.POSTS_DIR = dirs["posts"]
            mock_config.IMAGES_DIR = dirs["images"]
            mock_config.BASE_DIR = dirs["repo"]

            post = self._make_refined_post()
            path = save_draft(post)
            assert path.exists()
            assert path.name == "test-post.md"

            drafts = get_drafts()
            assert len(drafts) == 1

            found = get_draft("test-post")
            assert found is not None

    def test_approve_moves_to_posts(self, dirs):
        from backend.publishing.drafts import save_draft, approve_draft

        with patch("backend.publishing.drafts.Config") as mock_config:
            mock_config.DRAFTS_DIR = dirs["drafts"]
            mock_config.POSTS_DIR = dirs["posts"]
            mock_config.IMAGES_DIR = dirs["images"]
            mock_config.BASE_DIR = dirs["repo"]

            save_draft(self._make_refined_post())

        # Mock git operations for approve_draft -> commit_and_push
        with patch("backend.publishing.drafts.Config") as mock_config, \
             patch("backend.publishing.git.Config") as mock_git_config, \
             patch("backend.publishing.drafts.commit_and_push"):

            mock_config.DRAFTS_DIR = dirs["drafts"]
            mock_config.POSTS_DIR = dirs["posts"]
            mock_config.IMAGES_DIR = dirs["images"]
            mock_config.BASE_DIR = dirs["repo"]
            mock_git_config.BASE_DIR = dirs["repo"]

            dest = approve_draft("test-post")

            assert dest.exists()
            assert dest.parent == dirs["posts"]
            # Draft should no longer exist in drafts/
            assert not (dirs["drafts"] / "test-post.md").exists()

    def test_reject_deletes_draft(self, dirs):
        from backend.publishing.drafts import save_draft, reject_draft

        with patch("backend.publishing.drafts.Config") as mock_config:
            mock_config.DRAFTS_DIR = dirs["drafts"]
            mock_config.POSTS_DIR = dirs["posts"]
            mock_config.IMAGES_DIR = dirs["images"]
            mock_config.BASE_DIR = dirs["repo"]

            save_draft(self._make_refined_post())
            assert (dirs["drafts"] / "test-post.md").exists()

            reject_draft("test-post")

        assert not (dirs["drafts"] / "test-post.md").exists()

    def test_reject_with_images_cleans_up(self, dirs):
        from backend.publishing.drafts import save_draft, reject_draft

        # Create image directory alongside draft
        img_dir = dirs["images"] / "test-post"
        img_dir.mkdir(parents=True)
        (img_dir / "hero.webp").write_text("fake image")

        with patch("backend.publishing.drafts.Config") as mock_config:
            mock_config.DRAFTS_DIR = dirs["drafts"]
            mock_config.POSTS_DIR = dirs["posts"]
            mock_config.IMAGES_DIR = dirs["images"]
            mock_config.BASE_DIR = dirs["repo"]

            save_draft(self._make_refined_post())
            reject_draft("test-post")

        assert not img_dir.exists()


class TestDeletePost:
    """Test published post deletion flow."""

    def test_delete_removes_post_and_images(self, tmp_path):
        posts_dir = tmp_path / "posts"
        images_dir = tmp_path / "images"
        posts_dir.mkdir(parents=True)
        images_dir.mkdir(parents=True)

        (posts_dir / "old-post.md").write_text("---\ntags: ['test']\n---\n")
        img_dir = images_dir / "old-post"
        img_dir.mkdir(parents=True)
        (img_dir / "hero.webp").write_text("fake image")

        from backend.publishing.posts import delete_post

        with patch("backend.publishing.posts.Config") as mock_config, \
             patch("backend.publishing.git.run_git_command"):

            mock_config.POSTS_DIR = posts_dir
            mock_config.IMAGES_DIR = images_dir
            mock_config.BASE_DIR = tmp_path

            delete_post("old-post")

        assert not (posts_dir / "old-post.md").exists()
        assert not img_dir.exists()
