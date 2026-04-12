from openai import OpenAI
from utils.llm_config import LLM_CONFIG

COMMON_EXTENSIONS = {
    ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript",
    ".jsx": "JavaScript", ".tsx": "TypeScript", ".java": "Java",
    ".cs": "C#", ".go": "Go", ".rs": "Rust", ".rb": "Ruby",
    ".php": "PHP", ".kt": "Kotlin", ".swift": "Swift",
    ".cpp": "C++", ".c": "C", ".sh": "Shell", ".sql": "SQL",
    ".r": "R", ".scala": "Scala", ".dart": "Dart",
}


def detect_language(code, ext=None):
    hint = ""
    if ext and ext.lower() in COMMON_EXTENSIONS:
        hint = f"The file extension suggests this may be {COMMON_EXTENSIONS[ext.lower()]}. "

    system_prompt = (
        "Identify the programming language of this code snippet. "
        "Respond with ONLY the language name (e.g. Python, JavaScript, Go, Rust, SQL). "
        "If you cannot determine the language, respond with UNKNOWN."
    )
    user_content = f"{hint}\n\n{code}" if hint else code

    config = LLM_CONFIG["config_list"][0]
    client = OpenAI(
        base_url=config["base_url"],
        api_key=config["api_key"]
    )

    try:
        response = client.chat.completions.create(
            model=config["model"],
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            max_tokens=20,
        )
        result = response.choices[0].message.content.strip()
        return result if result else "UNKNOWN"
    except Exception:
        return "UNKNOWN"
