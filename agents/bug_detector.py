import autogen
from utils.llm_config import LLM_CONFIG


def create_bug_detector():
    """AssistantAgent that detects bugs in any programming language."""
    system_prompt = (
        "You are an expert bug detection specialist.\n"
        "You will receive a code snippet and its programming language.\n"
        "Identify bugs appropriate for that language: logical errors, off-by-one errors,\n"
        "null/undefined dereferences, incorrect variable usage, missing error handling,\n"
        "type mismatches, resource leaks, and potential runtime exceptions.\n"
        "Apply the common pitfalls and gotchas known for the specified language.\n"
        "Respond ONLY with a numbered list of findings (line reference + brief explanation).\n"
        "If no bugs found, respond with exactly: No bugs found.\n"
        "Do NOT suggest fixes. Do NOT repeat the code. Be concise."
    )
    return autogen.AssistantAgent(
        name="Bug_Detector",
        system_message=system_prompt,
        llm_config=LLM_CONFIG,
    )
