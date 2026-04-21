import os

from dotenv import load_dotenv


load_dotenv()


LLM_BASE_URL = os.getenv("LLM_BASE_URL")
LLM_MODEL = "openai/gpt-4.1-mini"
LLM_API_KEY = "no-key"

if not LLM_BASE_URL:
    raise ValueError("Missing required LLM environment variable: LLM_BASE_URL")


LLM_CONFIG = {
    "config_list": [{
        "model": LLM_MODEL,
        "base_url": LLM_BASE_URL,
        "api_key": LLM_API_KEY
    }],
    "cache_seed": None
}
