from .openrouter import OpenRouterProvider
from .base import AIProvider
from .gemini import GeminiProvider
from .claude import ClaudeProvider
from .openai import OpenAIProvider
from .groq import GroqProvider
from app import config


def get_provider() -> AIProvider:
    """Factory function to get the configured AI provider"""
    
    providers = {
        "gemini": GeminiProvider,
        "claude": ClaudeProvider,
        "openai": OpenAIProvider,
        "groq": GroqProvider,
        "openrouter": OpenRouterProvider  
    }
    
    provider_name = config.AI_PROVIDER
    
    if provider_name not in providers:
        raise ValueError(
            f"Unknown provider: {provider_name}. "
            f"Available: {', '.join(providers.keys())}"
        )
    
    try:
        return providers[provider_name]()
    except Exception as e:
        raise RuntimeError(
            f"Failed to initialize {provider_name} provider. "
            f"Check your API key in .env file. Error: {e}"
        )


__all__ = ['AIProvider', 'get_provider']
