import os
from dotenv import load_dotenv

load_dotenv()

# Provider selection
AI_PROVIDER = os.getenv("AI_PROVIDER", "claude").lower()

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Model configurations
MODELS = {
    "gemini": "gemini-2.0-flash-exp",
    "claude": "claude-sonnet-4-20250514",
    "openai": "gpt-4o-mini",
    "groq": "meta-llama/llama-4-scout-17b-16e-instruct",
    # "openrouter": "meta-llama/llama-4-maverick-17b-128e-instruct",
    # "openrouter": "google/gemini-2.0-flash-exp:free",
    # "openrouter": "qwen/qwen-2-vl-72b-instruct:free",
    "openrouter": "mistralai/mistral-large:free"
}
