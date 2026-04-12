import autogen
from utils.llm_config import LLM_CONFIG


def create_security_auditor():
    """AssistantAgent that audits security vulnerabilities for any programming language."""
    system_prompt = (
        "You are an application security expert.\n"
        "You will receive a code snippet and its programming language.\n"
        "Identify security vulnerabilities relevant to that language using OWASP guidelines\n"
        "and language-specific known risks (e.g. injection, insecure deserialization,\n"
        "hardcoded secrets, unsafe function use, improper input validation).\n"
        "Each finding must include: severity (HIGH / MEDIUM / LOW), line reference if possible,\n"
        "and a one-sentence explanation.\n"
        "Respond ONLY with a numbered list of findings.\n"
        "If no issues found, respond with exactly: No security issues found.\n"
        "Do NOT suggest exploit code. Be concise."
    )
    return autogen.AssistantAgent(
        name="Security_Auditor",
        system_message=system_prompt,
        llm_config=LLM_CONFIG,
    )
