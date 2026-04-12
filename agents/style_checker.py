import autogen
from utils.llm_config import LLM_CONFIG


def create_style_checker():
    """AssistantAgent that checks style violations for any programming language."""
    system_prompt = (
        "You are a code style expert.\n"
        "You will receive a code snippet and its programming language.\n"
        "Flag style violations according to the standard or most widely accepted style guide\n"
        "for the specified language (e.g. PEP 8 for Python, Google Style Guide for Java,\n"
        "Airbnb for JavaScript, etc.). If no official guide exists, apply widely accepted\n"
        "community conventions for that language.\n"
        "Respond ONLY with a numbered list of style issues (brief explanation per issue).\n"
        "If no issues found, respond with exactly: No style issues found.\n"
        "Do NOT suggest rewritten code. Be concise."
    )
    return autogen.AssistantAgent(
        name="Style_Checker",
        system_message=system_prompt,
        llm_config=LLM_CONFIG,
    )
