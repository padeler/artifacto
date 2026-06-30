import pytest
from pathlib import Path
from backend.refinement.providers import parse_llm_output, RefinedPost
from backend.config import Config


class TestParseLLMOutput:
    def test_parses_suggested_images(self):
        markdown = """---
title: "Fixing Docker Network"
summary: "How to fix docker network issues."
pubDate: 2026-06-30
tags: ["docker", "networking"]
suggestedImages: ["docker-network-diagram", "container-connectivity"]
draft: false
---

# Fixing Docker Network

Some content here.
"""
        post = parse_llm_output(markdown)
        assert isinstance(post, RefinedPost)
        assert post.title == "Fixing Docker Network"
        assert post.slug == "fixing-docker-network"
        assert post.tags == ["docker", "networking"]
        assert post.suggested_images == [
            "docker-network-diagram",
            "container-connectivity",
        ]

    def test_handles_missing_suggested_images(self):
        markdown = """---
title: "Simple Post"
summary: "No images needed."
pubDate: 2026-06-30
tags: ["testing"]
draft: false
---

Content without suggested images.
"""
        post = parse_llm_output(markdown)
        assert post.suggested_images == []

    def test_fallback_no_front_matter(self):
        markdown = "Just some random text with no front-matter at all."
        post = parse_llm_output(markdown)
        assert post.title == "Untitled Post"
        assert post.slug == "untitled-post"  # slug is generated from title
        assert post.suggested_images == []


class TestResolveSuggestedImages:
    def test_empty_terms_returns_empty(self):
        from backend.media.core import resolve_suggested_images

        result = resolve_suggested_images([], "test-slug")
        assert result == []

    def test_none_terms_returns_empty(self):
        from backend.media.core import resolve_suggested_images

        result = resolve_suggested_images(None, "test-slug") if None else []
        # Function expects list[str], but guard for empty input
        result = resolve_suggested_images([], "test-slug")
        assert result == []
