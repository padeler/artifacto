import re
from dataclasses import dataclass
from typing import Protocol
from pathlib import Path
import logging
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

def parse_llm_output(markdown_content: str) -> RefinedPost:
    """Parses the LLM markdown output to extract front-matter fields and body."""
    # Simple front-matter parsing
    title = "Untitled Post"
    summary = ""
    tags = []
    
    front_matter_match = re.search(r"^---\s*\n(.*?)\n---\s*\n(.*)", markdown_content, re.DOTALL)
    if front_matter_match:
        front_matter = front_matter_match.group(1)
        markdown_body = front_matter_match.group(2)
        
        # Extract title
        title_match = re.search(r"^title:\s*['\"]?(.*?)['\"]?$", front_matter, re.MULTILINE)
        if title_match:
            title = title_match.group(1).strip()
            
        # Extract summary
        summary_match = re.search(r"^summary:\s*['\"]?(.*?)['\"]?$", front_matter, re.MULTILINE)
        if summary_match:
            summary = summary_match.group(1).strip()
            
        # Extract tags
        tags_match = re.search(r"^tags:\s*\[(.*?)\]", front_matter, re.MULTILINE)
        if tags_match:
            tags_str = tags_match.group(1)
            tags = [t.strip().strip("'").strip('"') for t in tags_str.split(",") if t.strip()]
            
    else:
        logger.warning("Failed to parse front-matter from LLM output. Using raw output.")
        markdown_body = markdown_content

    # Generate slug from title
    slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')
    if not slug:
        slug = "draft-post"
        
    return RefinedPost(
        title=title,
        slug=slug,
        tags=tags,
        summary=summary,
        markdown_body=markdown_content.strip(),
        suggested_images=[] # For now, placeholder
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
