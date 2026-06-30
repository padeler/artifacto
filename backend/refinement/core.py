from pathlib import Path
from backend.config import Config
from backend.refinement.providers import (
    LLMProvider, 
    RefinedPost, 
    AnthropicAPIProvider, 
    OllamaProvider, 
    ClaudeCodeProvider
)
import logging

logger = logging.getLogger(__name__)

def get_llm_provider() -> LLMProvider:
    provider_name = Config.LLM_PROVIDER.lower()
    
    if provider_name == "anthropic_api":
        if not Config.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY is not set in environment.")
        return AnthropicAPIProvider(api_key=Config.ANTHROPIC_API_KEY)
        
    elif provider_name == "ollama":
        return OllamaProvider(model_name=Config.OLLAMA_MODEL)
        
    elif provider_name == "claude_code":
        return ClaudeCodeProvider()
        
    else:
        logger.warning(f"Unknown LLM_PROVIDER '{provider_name}'. Defaulting to ClaudeCodeProvider.")
        return ClaudeCodeProvider()

def refine_content(raw_text: str, existing_tags: list[str], images: list[Path]) -> RefinedPost:
    """
    Main entry point for refining content using the configured LLM provider.
    """
    provider = get_llm_provider()
    return provider.refine(raw_text, existing_tags, images)
