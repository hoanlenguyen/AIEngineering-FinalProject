# CodeSentinel — Claude Instructions

## Project Overview
CodeSentinel is a multi-agent code review CLI tool built with **AG2 (ag2 package)**.
It reviews source code in **any programming language** using a GroupChat orchestration pattern.
It supports three input modes: inline paste, single file, or an entire project directory.
The system detects the programming language automatically, runs three specialist review agents,
and synthesizes their findings into a structured report saved to disk.

## Architecture
- **Orchestration:** AG2 `GroupChat` with a custom `speaker_selection_func`
- **Agent execution order:** `User_Proxy` → `Bug_Detector` → `Style_Checker` → `Security_Auditor` → `Summarizer`
- **Tool call:** `Summarizer` calls `save_review_to_file`, executed by `User_Proxy`
- **Termination:** Chat ends when `Summarizer` outputs `REVIEW COMPLETE`
- **Project mode:** specialist agents run once per file; Summarizer runs once at the end across all findings

## File Structure
```
codesentinenl/
├── CLAUDE.md
├── main.py                        # Entry point: --inline | --file | --project CLI args
├── requirements.txt               # ag2, openai
├── review_output.md               # Generated report (do not edit manually)
├── agents/
│   ├── bug_detector.py            # AssistantAgent — language-agnostic bug detection
│   ├── style_checker.py           # AssistantAgent — language-agnostic style checking
│   ├── security_auditor.py        # AssistantAgent — language-agnostic security audit
│   ├── summarizer.py              # AssistantAgent — synthesizes report, calls save tool
│   └── user_proxy.py              # UserProxyAgent — initiates chat, executes tools
├── tools/
│   └── save_report.py             # save_review_to_file(report: str) -> str
├── utils/
│   ├── input_handler.py           # Resolves --inline, --file, --project to tuple list
│   ├── language_detector.py       # detect_language(code, ext) -> str (any language)
│   ├── file_scanner.py            # Scans project dir, returns (path, content, language) list
│   └── llm_config.py              # LLM_CONFIG dict for AG2
└── tests/
    ├── test_sample.py
    ├── test_sample.js
    ├── TestSample.java
    └── TestSample.cs
```

## Commands
- **Install:** `pip install -r requirements.txt`
- **Run (inline):** `python main.py --inline` — paste code, type `END` on a new line to finish
- **Run (file):** `python main.py --file path/to/code.py`
- **Run (project):** `python main.py --project path/to/project/`
- **Test single file:** `python main.py --file tests/test_sample.py`
- **Test project:** `python main.py --project tests/`

## Input Modes — Detailed Behaviour

### --inline
- Prompt user to paste code in terminal
- Terminated by a line containing only `END`
- Call `detect_language(code=snippet, ext=None)` — LLM detection
- If UNKNOWN, prompt user to enter language manually
- Return [('Inline snippet', snippet, language)]

### --file
- Extract extension with `os.path.splitext`
- Read file content with `open(path, encoding='utf-8')`
- Call `detect_language(code=content, ext=extension)` — extension hint + LLM
- If UNKNOWN, prompt user to enter language manually
- Return [(filename, content, language)]

### --project
- Call `scan_project(directory)` from `utils/file_scanner.py`
- Returns list of `(relative_filepath, content, language)` tuples
- Cap at **20 files** — warn user if more found
- For each file: run Bug_Detector, Style_Checker, Security_Auditor and collect findings
- After all files: run Summarizer ONCE with all per-file findings combined
- Save combined report to `review_output.md`

## Language Detection — General Approach

### Common extension hints (pass as `ext` to help the LLM confirm)
```python
COMMON_EXTENSIONS = {
    ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript",
    ".jsx": "JavaScript", ".tsx": "TypeScript", ".java": "Java",
    ".cs": "C#", ".go": "Go", ".rs": "Rust", ".rb": "Ruby",
    ".php": "PHP", ".kt": "Kotlin", ".swift": "Swift",
    ".cpp": "C++", ".c": "C", ".sh": "Shell", ".sql": "SQL",
    ".r": "R", ".scala": "Scala", ".dart": "Dart",
}
```

### detect_language(code, ext=None) -> str
- If `ext` is in `COMMON_EXTENSIONS`, pass that as a hint to the LLM prompt (still confirm via LLM)
- LLM system prompt: "Identify the programming language of this code snippet.
  Respond with ONLY the language name (e.g. Python, JavaScript, Go, Rust, SQL).
  If you cannot determine the language, respond with UNKNOWN."
- Return the LLM response as-is (trimmed) — do NOT restrict to a fixed list
- Return `UNKNOWN` only on API error or empty response

### File Scanner — which files to include
- Include files whose extension is in `COMMON_EXTENSIONS`
- Also include any file with a code-like extension not in the map — pass to LLM detector
- Skip: `.json`, `.yaml`, `.yml`, `.toml`, `.env`, `.xml`, `.md`, `.txt`, `.lock`, `.csv`
- Skip directories: `node_modules`, `__pycache__`, `.git`, `venv`, `.venv`, `env`,
  `dist`, `build`, `target`, `bin`, `obj`, `.idea`, `.vscode`
- Skip files larger than **100 KB**
- Do not follow symlinks
- Cap at **20 files**

## API Configuration
- **Base URL:** `https://5f5832nb90.execute-api.eu-central-1.amazonaws.com/v1`
- **Format:** OpenAI chat completions compatible
- **API key:** `no-key` (no authentication required)
- **Model:** `openai/gpt-4.1-mini`
- **NEVER** use environment variable auth — always pass `api_key='no-key'` directly

## LLM Config Pattern (AG2)
```python
LLM_CONFIG = {
    "config_list": [{
        "model": "openai/gpt-4.1-mini",
        "base_url": "https://5f5832nb90.execute-api.eu-central-1.amazonaws.com/v1",
        "api_key": "no-key"
    }],
    "cache_seed": None
}
```

## AG2 Patterns
- Import agents from `autogen` (AG2's package is `ag2` but imports as `autogen`)
- Register tools: `ag2.register_function(func, caller=summarizer, executor=user_proxy)`
- `UserProxyAgent` must have `code_execution_config=False` — never execute user code
- `human_input_mode="NEVER"` on UserProxy
- `is_termination_msg=lambda msg: "REVIEW COMPLETE" in (msg.get("content") or "")`
- `GroupChatManager` needs `llm_config=LLM_CONFIG`

## Agent System Prompts — Language-Agnostic Design

All three specialist agents follow the same pattern:
- They receive the code snippet and the detected language name
- They apply best practices, common conventions, and known vulnerability patterns
  **for whatever language is specified** — no hardcoded rules per language
- The LLM's training knowledge covers the conventions for each language automatically

### Bug_Detector system prompt
```
You are an expert bug detection specialist.
You will receive a code snippet and its programming language.
Identify bugs appropriate for that language: logical errors, off-by-one errors,
null/undefined dereferences, incorrect variable usage, missing error handling,
type mismatches, resource leaks, and potential runtime exceptions.
Apply the common pitfalls and gotchas known for the specified language.
Respond ONLY with a numbered list of findings (line reference + brief explanation).
If no bugs found, respond with exactly: No bugs found.
Do NOT suggest fixes. Do NOT repeat the code. Be concise.
```

### Style_Checker system prompt
```
You are a code style expert.
You will receive a code snippet and its programming language.
Flag style violations according to the standard or most widely accepted style guide
for the specified language (e.g. PEP 8 for Python, Google Style Guide for Java,
Airbnb for JavaScript, etc.). If no official guide exists, apply widely accepted
community conventions for that language.
Respond ONLY with a numbered list of style issues (brief explanation per issue).
If no issues found, respond with exactly: No style issues found.
Do NOT suggest rewritten code. Be concise.
```

### Security_Auditor system prompt
```
You are an application security expert.
You will receive a code snippet and its programming language.
Identify security vulnerabilities relevant to that language using OWASP guidelines
and language-specific known risks (e.g. injection, insecure deserialization,
hardcoded secrets, unsafe function use, improper input validation).
Each finding must include: severity (HIGH / MEDIUM / LOW), line reference if possible,
and a one-sentence explanation.
Respond ONLY with a numbered list of findings.
If no issues found, respond with exactly: No security issues found.
Do NOT suggest exploit code. Be concise.
```

### Summarizer system prompt
```
You are a senior code reviewer.
Synthesize findings from Bug_Detector, Style_Checker, and Security_Auditor
into a structured report.

For a single file or inline snippet use:
## File: <filename or 'Inline snippet'>
## Language: <language>
## Summary
[2-3 sentence overall assessment]
## Critical Issues (Must Fix)
[bugs + HIGH security findings, numbered]
## Recommended Improvements
[style + MEDIUM/LOW security findings, numbered]
## Verdict: PASS | PASS WITH NOTES | NEEDS REVISION

For a project review, produce one section per file in the above format, then add:
## Overall Project Verdict
[2-3 sentence summary]
PASS | PASS WITH NOTES | NEEDS REVISION

After writing the complete report, call save_review_to_file with the full report text.
Then output exactly: REVIEW COMPLETE

You only speak after all three specialist agents have contributed.
```

## Tool: save_review_to_file
- Signature: `save_review_to_file(report: str) -> str`
- Writes to `review_output.md` in CWD (always overwrites)
- Prepends `# CodeSentinel Review Report\n\n`
- Returns `'Report saved to review_output.md'` on success
- Fixed output path only — never accept dynamic paths from agent output

## Speaker Selection Logic
```python
def speaker_selection_func(last_speaker, groupchat):
    name = last_speaker.name
    agents = {a.name: a for a in groupchat.agents}
    order = ["User_Proxy", "Bug_Detector", "Style_Checker", "Security_Auditor", "Summarizer"]
    if name in order[:-1]:
        return agents[order[order.index(name) + 1]]
    return None
```

## Coding Conventions
- All agent factory functions named `create_<agent_name>()`, return the agent instance
- All imports use absolute paths from project root
- No f-string multiline system prompts — assign to a variable first
- `main.py` prints progress between steps
- `review_output.md` always overwritten on each run
- For `--project` mode, print `[Reviewing file X/N: filename]` before each file

## Do Not
- Do not hardcode language-specific rules in agent prompts — keep agents language-agnostic
- Do not restrict language detection to a fixed list — accept whatever the LLM returns
- Do not use `speaker_selection_method="round_robin"` — always use the custom function
- Do not add retry logic to LLM calls — the proxy handles this
- Do not store code in a global variable — pass through the chat message
- Do not create output files beyond `review_output.md`
- Do not use `subprocess`, `os.system`, or any shell execution
- Do not review config/data files (`.json`, `.yaml`, `.env`, `.xml`, `.csv`, `.md`)
- Do not follow symlinks when scanning project directories
