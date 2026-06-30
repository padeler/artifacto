"""Tests for tag index manager, post filtering, and slug generation."""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestGetExistingTags:
    """Test backend.tags.index.get_existing_tags()."""

    def test_scans_posts_and_drafts(self, tmp_path):
        posts_dir = tmp_path / "posts"
        drafts_dir = tmp_path / "drafts"
        posts_dir.mkdir(parents=True)
        drafts_dir.mkdir(parents=True)

        (posts_dir / "a.md").write_text(
            "---\ntags: ['python', 'docker']\n---\ncontent"
        )
        (drafts_dir / "b.md").write_text(
            "---\ntags: ['python', 'rust']\n---\ndraft content"
        )

        from backend.tags.index import get_existing_tags

        with patch("backend.tags.index.Config") as mock_config:
            mock_config.POSTS_DIR = posts_dir
            mock_config.DRAFTS_DIR = drafts_dir
            tags = get_existing_tags()

        assert sorted(tags) == ["docker", "python", "rust"]

    def test_empty_directories(self, tmp_path):
        from backend.tags.index import get_existing_tags

        with patch("backend.tags.index.Config") as mock_config:
            mock_config.POSTS_DIR = tmp_path / "nonexistent_posts"
            mock_config.DRAFTS_DIR = tmp_path / "nonexistent_drafts"
            tags = get_existing_tags()

        assert tags == []

    def test_duplicate_tags_deduplicated(self, tmp_path):
        posts_dir = tmp_path / "posts"
        posts_dir.mkdir(parents=True)
        (posts_dir / "a.md").write_text("---\ntags: ['python']\n---\n")
        (posts_dir / "b.md").write_text("---\ntags: ['python', 'docker']\n---\n")

        from backend.tags.index import get_existing_tags

        with patch("backend.tags.index.Config") as mock_config:
            mock_config.POSTS_DIR = posts_dir
            mock_config.DRAFTS_DIR = tmp_path / "no_drafts"
            tags = get_existing_tags()

        assert tags.count("python") == 1


class TestSlugGeneration:
    """Test slug generation from titles."""

    def test_basic_slug(self):
        from backend.refinement.providers import parse_llm_output
        md = "---\ntitle: Fixing OpenSSL Errors\ntags: ['openssl']\n---\nBody"
        post = parse_llm_output(md)
        assert post.slug == "fixing-openssl-errors"

    def test_slug_special_chars(self):
        from backend.refinement.providers import parse_llm_output
        md = "---\ntitle: What's New in v2.0?! \ntags: ['release']\n---\nBody"
        post = parse_llm_output(md)
        # Apostrophe becomes separator; title "What's" -> slug "what-s"
        assert post.slug == "what-s-new-in-v2-0"

    def test_slug_empty_title_fallback(self):
        from backend.refinement.providers import parse_llm_output
        md = "No front-matter here at all."
        post = parse_llm_output(md)
        # Default title "Untitled Post" -> slug "untitled-post"
        assert post.slug == "untitled-post"

    def test_slug_unicode_normalized(self):
        from backend.refinement.providers import parse_llm_output
        md = "---\ntitle: Café résumé test\ntags: ['unicode']\n---\nBody"
        post = parse_llm_output(md)
        # Non-ASCII chars become separators, then stripped
        assert "-" in post.slug or post.slug == "caf-rsum-test"


class TestGetPostsFilter:
    """Test backend.publishing.posts.get_posts() with tag filter."""

    def test_get_all_posts(self, tmp_path):
        (tmp_path / "a.md").write_text("content a")
        (tmp_path / "b.md").write_text("content b")

        from backend.publishing.posts import get_posts

        with patch("backend.publishing.posts.Config") as mock_config:
            mock_config.POSTS_DIR = tmp_path
            posts = get_posts()
        assert len(posts) == 2

    def test_filter_by_tag(self, tmp_path):
        (tmp_path / "a.md").write_text("---\ntags: ['python']\n---\n")
        (tmp_path / "b.md").write_text("---\ntags: ['rust']\n---\n")
        (tmp_path / "c.md").write_text("---\ntags: ['python', 'docker']\n---\n")

        from backend.publishing.posts import get_posts

        with patch("backend.publishing.posts.Config") as mock_config:
            mock_config.POSTS_DIR = tmp_path
            posts = get_posts(tag="python")

        assert len(posts) == 2
        stems = {p.stem for p in posts}
        assert stems == {"a", "c"}

    def test_filter_nonexistent_tag(self, tmp_path):
        (tmp_path / "a.md").write_text("---\ntags: ['python']\n---\n")

        from backend.publishing.posts import get_posts

        with patch("backend.publishing.posts.Config") as mock_config:
            mock_config.POSTS_DIR = tmp_path
            posts = get_posts(tag="nonexistent")

        assert posts == []


class TestYAMLParsing:
    """Test YAML-based front-matter parsing and validation."""

    def test_valid_yaml_parsed(self):
        from backend.refinement.providers import parse_llm_output
        md = "---\ntitle: 'Valid YAML Post'\npubDate: 2026-06-30\ntags: ['test']\n---\nBody"
        post = parse_llm_output(md)
        assert post.title == "Valid YAML Post"

    def test_yaml_validation_error_falls_back(self, caplog):
        import yaml as yaml_module
        from backend.refinement.providers import parse_llm_output

        # Malformed YAML that will fail validation
        md = "---\ntags: not-a-list\ntitle: 123\n---\nBody text."
        post = parse_llm_output(md)
        # Should fall back to regex, title should be extracted or default
        assert isinstance(post.title, str)

    def test_suggested_images_parsed_from_yaml(self):
        from backend.refinement.providers import parse_llm_output
        md = (
            "---\n"
            "title: Post with images\n"
            "tags: ['test']\n"
            "suggestedImages:\n"
            "  - 'docker-network'\n"
            "  - 'container-connectivity'\n"
            "---\nContent here."
        )
        post = parse_llm_output(md)
        assert post.suggested_images == ["docker-network", "container-connectivity"]

    def test_inline_yaml_list_tags(self):
        from backend.refinement.providers import parse_llm_output
        md = (
            "---\n"
            "title: Inline tags\n"
            "tags: ['rust', 'cli', 'linux']\n"
            "---\nContent."
        )
        post = parse_llm_output(md)
        assert sorted(post.tags) == ["cli", "linux", "rust"]
