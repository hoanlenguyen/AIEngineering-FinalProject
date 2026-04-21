import os

from dotenv import load_dotenv


load_dotenv()


LLM_MODEL = os.getenv("LLM_MODEL")
LLM_BASE_URL = os.getenv("LLM_BASE_URL")
LLM_API_KEY = os.getenv("LLM_API_KEY", "no-key")

if not LLM_MODEL or not LLM_BASE_URL:
    raise ValueError("Missing required LLM environment variables: LLM_MODEL and LLM_BASE_URL")


LLM_CONFIG = {
    "config_list": [{
        "model": LLM_MODEL,
        "base_url": LLM_BASE_URL,
        "api_key": LLM_API_KEY
    }],
    "cache_seed": None
}
