import re
from dataclasses import dataclass
from typing import Protocol
from pathlib import Path
import logging

import yaml

from backend.config import Config

logger = logging.getLogger(__name__)

@dataclass
class RefinedPost:
    title: str
    slug: str
    tags: list[str]
    summary: str
    markdown_body: str
    suggested_images: list[str]

class LLMProvider(Protocol):
    def refine(self, raw_text: str, existing_tags: list[str], images: list[Path]) -> RefinedPost:
        ...

def _validate_frontmatter(data: dict) -> None:
    """Validate that front-matter contains required fields."""
    if "title" not in data or not isinstance(data["title"], str):
        raise ValueError("Front-matter missing or invalid 'title' field (must be string)")
    if "tags" in data and not isinstance(data["tags"], list):
        raise ValueError("Front-matter 'tags' field must be a list")
    if "suggestedImages" in data and not isinstance(data["suggestedImages"], list):
        raise ValueError("Front-matter 'suggestedImages' field must be a list")


def parse_llm_output(markdown_content: str) -> RefinedPost:
    """Parses the LLM markdown output to extract front-matter fields and body.

    Uses PyYAML for robust front-matter parsing with validation. Falls back
    to heuristic extraction if YAML parsing fails or no front-matter is present.
    """
    title = "Untitled Post"
    summary = ""
    tags: list[str] = []
    suggested_images: list[str] = []
    markdown_body = ""

    # Extract front-matter block between --- delimiters
    front_matter_match = re.search(
        r"^---\s*\n(.*?)\n---\s*\n(.*)", markdown_content, re.DOTALL
    )
    if not front_matter_match:
        logger.warning("No front-matter delimiters (---) found. Using heuristic draft mode.")
        markdown_body = markdown_content
        # Try to extract a title from the first heading
        heading_match = re.search(r"^##+\s+(.+)", markdown_content, re.MULTILINE)
        if heading_match:
            title = heading_match.group(1).strip()[:120]

    else:
        front_matter_text = front_matter_match.group(1)
        markdown_body = front_matter_match.group(2)

        try:
            fm_data = yaml.safe_load(front_matter_text)
            if not isinstance(fm_data, dict):
                raise ValueError("Front-matter did not parse as a YAML mapping (dict)")
            _validate_frontmatter(fm_data)

            title = fm_data.get("title", "Untitled Post")
            summary = fm_data.get("summary", "")
            tags = [str(t).strip().lower() for t in fm_data.get("tags", [])]
            suggested_images = [
                str(i).strip() for i in fm_data.get("suggestedImages", [])
            ]

        except (yaml.YAMLError, ValueError) as e:
            logger.warning(f"YAML front-matter validation/parsing failed ({e}). Using regex fallback.")
            # Regex fallback for individual fields
            title_match = re.search(
                r"^title:\s*['\"]?(.*?)['\"]?$", front_matter_text, re.MULTILINE
            )
            if title_match:
                title = title_match.group(1).strip()

            summary_match = re.search(
                r"^summary:\s*['\"]?(.*?)['\"]?$", front_matter_text, re.MULTILINE
            )
            if summary_match:
                summary = summary_match.group(1).strip()

            tags_match = re.search(r"^tags:\s*\[(.*?)\]", front_matter_text, re.MULTILINE)
            if tags_match:
                tags_str = tags_match.group(1)
                tags = [t.strip().strip("'").strip('"') for t in tags_str.split(",") if t.strip()]

            images_match = re.search(
                r"^suggestedImages:\s*\[(.*?)\]", front_matter_text, re.MULTILINE
            )
            if images_match:
                images_str = images_match.group(1)
                suggested_images = [
                    i.strip().strip("'").strip('"')
                    for i in images_str.split(",")
                    if i.strip()
                ]

    # Generate slug from title
    slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-') or "draft-post"

    return RefinedPost(
        title=title,
        slug=slug,
        tags=tags,
        summary=summary,
        markdown_body=markdown_content.strip(),
        suggested_images=suggested_images,
    )

class AnthropicAPIProvider:
    def __init__(self, api_key: str):
        try:
            from anthropic import Anthropic
            self.client = Anthropic(api_key=api_key)
        except ImportError:
            raise ImportError("Anthropic SDK not installed. Run pip install anthropic")

    def refine(self, raw_text: str, existing_tags: list[str], images: list[Path]) -> RefinedPost:
        from backend.refinement.prompt import build_prompt
        
        prompt = build_prompt(raw_text, existing_tags, [str(p) for p in images])
        
        logger.info("Calling Anthropic API for refinement...")
        response = self.client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=4000,
            system="You are an expert technical writer. Output ONLY valid markdown with front-matter. No pleasantries.",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        content = response.content[0].text
        return parse_llm_output(content)

class OllamaProvider:
    def __init__(self, model_name: str, base_url: str = "http://localhost:11434"):
        self.model_name = model_name
        self.base_url = base_url

    def refine(self, raw_text: str, existing_tags: list[str], images: list[Path]) -> RefinedPost:
        import httpx
        from backend.refinement.prompt import build_prompt
        
        prompt = build_prompt(raw_text, existing_tags, [str(p) for p in images])
        
        logger.info(f"Calling Ollama API (model: {self.model_name}) for refinement...")
        
        # We need a synchronous call or we can use asyncio.run if this is async. 
        # For simplicity, using httpx sync client.
        try:
            with httpx.Client(timeout=120.0) as client:
                response = client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model_name,
                        "prompt": prompt,
                        "system": "You are an expert technical writer. Output ONLY valid markdown with front-matter. No pleasantries.",
                        "stream": False
                    }
                )
                response.raise_for_status()
                content = response.json().get("response", "")
                return parse_llm_output(content)
        except Exception as e:
            logger.error(f"Ollama API call failed: {e}")
            raise

class ClaudeCodeProvider:
    def __init__(self):
        self._fallback_providers: list[LLMProvider] = []
        # Try to add Anthropic as first fallback if key is available
        if Config.ANTHROPIC_API_KEY:
            try:
                self._fallback_providers.append(
                    AnthropicAPIProvider(api_key=Config.ANTHROPIC_API_KEY)
                )
                logger.info("ClaudeCodeProvider: Anthropic API available as fallback.")
            except ImportError:
                logger.debug("Anthropic SDK not installed — skipping as fallback.")
        # Try Ollama as secondary fallback
        self._fallback_providers.append(OllamaProvider(model_name=Config.OLLAMA_MODEL))
        logger.info(f"ClaudeCodeProvider initialized with {len(self._fallback_providers)} fallback provider(s).")

    def refine(self, raw_text: str, existing_tags: list[str], images: list[Path]) -> RefinedPost:
        """
        When running under Claude Code, the agent handles refinement directly.
        This provider attempts configured fallback LLM providers first; if all fail,
        it produces a basic RefinedPost from heuristics so the CLI doesn't crash.
        """
        logger.info("ClaudeCodeProvider refine invoked — trying fallback providers...")

        last_error: Exception | None = None
        for provider in self._fallback_providers:
            try:
                return provider.refine(raw_text, existing_tags, images)
            except Exception as e:
                last_error = e
                logger.warning(f"ClaudeCodeProvider fallback failed: {e}")

        # All fallbacks exhausted — produce a basic post heuristically
        logger.warning(
            f"All fallback providers exhausted (last error: {last_error}). "
            "Producing heuristic draft."
        )
        title = self._extract_title(raw_text)
        slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-') or "draft-post"

        return RefinedPost(
            title=title,
            slug=slug,
            tags=[],
            summary="",
            markdown_body=raw_text.strip(),
            suggested_images=[],
        )

    @staticmethod
    def _extract_title(text: str) -> str:
        """Extract the first H1 or H2 heading, or fall back to the first line."""
        heading_match = re.search(r"^##+\s+(.+)", text, re.MULTILINE)
        if heading_match:
            return heading_match.group(1).strip()
        first_line = text.split("\n")[0].strip()
        return first_line[:120] if first_line else "Untitled Draft"
