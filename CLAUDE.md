# CodeSentinel — Claude Instructions

## Project Overview
CodeSentinel is a multi-agent code review tool built with **AG2 (ag2 package)**.
It reviews source code in **any programming language** using a GroupChat orchestration pattern.
It supports three input modes: inline paste, single file upload, or a local project directory path.
A **Flask web UI** serves as the frontend — users interact via browser at `localhost:5000`.
The system detects the programming language automatically, runs three specialist review agents,
and displays the findings as a rendered markdown report in the browser.

## Architecture
- **Orchestration:** AG2 `GroupChat` with a custom `speaker_selection_func`
- **Agent execution order:** `User_Proxy` → `Bug_Detector` → `Style_Checker` → `Security_Auditor` → `Summarizer`
- **Tool call:** `Summarizer` calls `save_review_to_file`, executed by `User_Proxy`
- **Termination:** Chat ends when `Summarizer` outputs `REVIEW COMPLETE`
- **Project mode:** specialist agents run once per file; Summarizer runs once at the end
- **UI:** Flask serves `index.html`; routes call agents directly in the same process
- **Progress:** Server-Sent Events (SSE) stream agent progress to the browser in real time

## File Structure
```
codesentinenl/
├── CLAUDE.md
├── app.py                         # Flask app — routes, SSE progress, agent orchestration
├── main.py                        # CLI entry point (kept for non-UI use)
├── requirements.txt               # ag2, openai, flask
├── review_output.md               # Generated report (saved by Summarizer tool)
├── templates/
│   └── index.html                 # Single-page UI: input panel + progress + results
├── static/
│   └── style.css                  # UI styling
├── agents/
│   ├── bug_detector.py
│   ├── style_checker.py
│   ├── security_auditor.py
│   ├── summarizer.py
│   └── user_proxy.py
├── tools/
│   └── save_report.py
├── utils/
│   ├── input_handler.py           # Used by CLI only
│   ├── language_detector.py
│   ├── file_scanner.py
│   └── llm_config.py
└── tests/
    ├── test_sample.py
    ├── test_sample.js
    ├── TestSample.java
    └── TestSample.cs
```

## Commands
- **Install:** `pip install -r requirements.txt`
- **Run UI:** `python app.py` → open `http://localhost:5000`
- **Run CLI (file):** `python main.py --file path/to/code.py`
- **Run CLI (inline):** `python main.py --inline`
- **Run CLI (project):** `python main.py --project path/to/project/`

## Flask App — app.py

### Routes
| Method | Route | Purpose |
|---|---|---|
| GET | `/` | Serve `index.html` |
| POST | `/review/inline` | Receive pasted code JSON, run agents, return report |
| POST | `/review/file` | Receive uploaded file, run agents, return report |
| POST | `/review/project` | Receive folder path string, scan + run agents, return report |
| GET | `/progress` | SSE endpoint — streams agent progress events to browser |

### Request/Response format
All `/review/*` routes accept JSON (or multipart for file upload) and return JSON:
```json
// Request (inline)
{ "code": "...", "language": "auto" }

// Request (project)
{ "path": "/absolute/or/relative/path/to/project" }

// Response (all routes)
{
  "report": "## File: ...\n## Language: ...\n...",
  "language": "Python",
  "verdict": "NEEDS REVISION",
  "saved_to": "review_output.md"
}
```

### SSE Progress Events
Use Flask's `Response` with `mimetype='text/event-stream'` and a generator function.
Emit one event per agent step. The browser listens and updates the progress strip.

```python
# Progress event format
data: {"step": "Bug_Detector", "status": "running"}
data: {"step": "Bug_Detector", "status": "done"}
data: {"step": "Style_Checker", "status": "running"}
# ... etc
data: {"step": "complete", "status": "done"}
```

Use a `queue.Queue` shared between the review thread and the SSE generator.
The review runs in a background thread; each agent completion pushes an event to the queue.
The SSE generator yields from the queue until the `complete` event is received.

### Agent orchestration in app.py
Import and call agents the same way as `main.py`.
For `/review/file`: save the uploaded file to a temp path, detect language, run agents, delete temp file.
For `/review/project`: validate the path exists on the server, call `scan_project()`, run agents per file.
For all routes: after agents finish, read `review_output.md` and return its contents in the response.

### Error handling
- If path does not exist (project mode): return `{"error": "Path not found"}` with HTTP 400
- If language is UNKNOWN and user did not specify: return `{"error": "Could not detect language"}` with HTTP 400
- If agent run fails: return `{"error": "Agent error: <message>"}` with HTTP 500
- Never expose raw Python tracebacks to the browser

## UI — templates/index.html

### Layout
Two-column layout:
- **Left panel (40%):** Input controls
- **Right panel (60%):** Progress strip + Report output

### Left panel — Input controls
Three tabs: **Inline** | **File** | **Project**

**Inline tab:**
- `<textarea>` for pasting code (min 15 rows, monospace font)
- Language selector dropdown: `Auto-detect` (default) + common languages as manual override
  (Python, JavaScript, TypeScript, Java, C#, Go, Rust, Ruby, PHP, Kotlin, Swift, C/C++, SQL, Shell, Other)

**File tab:**
- `<input type="file">` — accept any file (no extension restriction in HTML, server validates)
- Language selector dropdown (same as above, default Auto-detect)

**Project tab:**
- `<input type="text">` for local folder path (e.g. `/home/user/myproject`)
- Helper text: "Enter an absolute path to a project folder on this machine"
- Note: shows a warning that only up to 20 source files will be reviewed

**Shared:**
- `Review` button — triggers the appropriate fetch call based on active tab
- Button shows spinner and is disabled while a review is in progress

### Right panel — Progress + Results

**Progress strip** (shown during review, hidden otherwise):
Five steps shown as a horizontal stepper:
`Detecting Language` → `Bug Detector` → `Style Checker` → `Security Auditor` → `Summarizing`
Each step has three states: pending (grey) / running (blue spinner) / done (green checkmark)
Updated in real time via SSE.

**Results area** (shown after review completes):
- **Verdict badge** at the top — color coded:
  - 🟢 PASS — green background
  - 🟡 PASS WITH NOTES — yellow background
  - 🔴 NEEDS REVISION — red background
- **Rendered markdown report** — use `marked.js` (CDN) to render the report string as HTML
- **Download Report** button — triggers download of `review_output.md` via a `/download` route
- **New Review** button — clears results and resets the form

### JavaScript behaviour
- On `Review` click: disable button, show progress strip, clear old results
- Open an `EventSource` to `/progress` to receive SSE updates
- Send review request via `fetch` to the appropriate `/review/*` route
- On response: close SSE, hide progress strip, render report with `marked.parse(report)`,
  extract verdict from report text, show verdict badge, show results area
- On error: show error message in the results area, re-enable button

### marked.js CDN
```html
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
```
No other external JS dependencies needed.

## UI Styling — static/style.css
- Clean, minimal design — white background, light grey panel borders
- Monospace font for the code textarea (`font-family: 'Courier New', monospace`)
- Tab switcher: active tab has blue bottom border
- Progress stepper: horizontal flexbox, steps connected by a line
- Verdict badge: bold text, rounded corners, colour based on verdict value
- Report area: rendered markdown with sensible line spacing and code block styling
- Responsive: panels stack vertically on screens narrower than 768px

## requirements.txt
```
ag2
openai
flask
```

## Input Modes — Detailed Behaviour (same as CLI)

### Inline
- Detect language from pasted code via LLM (or use manual override if provided)
- Run single GroupChat review cycle

### File upload
- Save uploaded file to `tempfile.NamedTemporaryFile`
- Detect language from extension + LLM
- Run single GroupChat review cycle
- Delete temp file after review

### Project path
- Validate path exists with `os.path.isdir`
- Call `scan_project(path)` — returns list of (filepath, content, language)
- Cap at 20 files, warn if more found
- Run specialist agents per file, Summarizer once at end

## Language Detection — General Approach

### Common extension hints
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
- If `ext` is in `COMMON_EXTENSIONS`, pass as hint to LLM prompt
- LLM: "Identify the programming language. Respond with ONLY the language name or UNKNOWN."
- Return trimmed LLM response — do NOT restrict to a fixed list
- Return `UNKNOWN` on API error or empty response

## File Scanner Rules
- Walk directory recursively, include files with extensions in `COMMON_EXTENSIONS`
- Skip: `node_modules`, `__pycache__`, `.git`, `venv`, `.venv`, `env`, `dist`,
  `build`, `target`, `bin`, `obj`, `.idea`, `.vscode`
- Skip config/data files: `.json`, `.yaml`, `.yml`, `.toml`, `.env`, `.xml`, `.md`, `.txt`, `.lock`, `.csv`
- Skip files > 100 KB
- Do not follow symlinks
- Cap at 20 files

## API Configuration
- Load `LLM_BASE_URL`, `LLM_MODEL`, and `LLM_API_KEY` from `.env`

## LLM Config (AG2)
```python
LLM_CONFIG = {
    "config_list": [{
        "model": os.getenv("LLM_MODEL"),
        "base_url": os.getenv("LLM_BASE_URL"),
        "api_key": os.getenv("LLM_API_KEY", "no-key")
    }],
    "cache_seed": None
}
```

## AG2 Patterns
- Import agents from `autogen` (package is `ag2`, imports as `autogen`)
- `UserProxyAgent`: `code_execution_config=False`, `human_input_mode="NEVER"`
- `is_termination_msg=lambda msg: "REVIEW COMPLETE" in (msg.get("content") or "")`
- `GroupChatManager` needs `llm_config=LLM_CONFIG`
- Register tool: `ag2.register_function(save_review_to_file, caller=summarizer, executor=user_proxy)`

## Agent System Prompts — Language-Agnostic

### Bug_Detector
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

### Style_Checker
```
You are a code style expert.
You will receive a code snippet and its programming language.
Flag style violations according to the standard or most widely accepted style guide
for the specified language. If no official guide exists, apply widely accepted
community conventions for that language.
Respond ONLY with a numbered list of style issues (brief explanation per issue).
If no issues found, respond with exactly: No style issues found.
Do NOT suggest rewritten code. Be concise.
```

### Security_Auditor
```
You are an application security expert.
You will receive a code snippet and its programming language.
Identify security vulnerabilities relevant to that language using OWASP guidelines
and language-specific known risks (injection, insecure deserialization,
hardcoded secrets, unsafe function use, improper input validation).
Each finding: severity (HIGH / MEDIUM / LOW), line reference if possible,
one-sentence explanation.
Respond ONLY with a numbered list of findings.
If no issues found, respond with exactly: No security issues found.
Do NOT suggest exploit code. Be concise.
```

### Summarizer
```
You are a senior code reviewer.
Synthesize findings from Bug_Detector, Style_Checker, and Security_Auditor
into a structured report.

For a single file or inline snippet:
## File: <filename or 'Inline snippet'>
## Language: <language>
## Summary
[2-3 sentences]
## Critical Issues (Must Fix)
[bugs + HIGH security findings, numbered]
## Recommended Improvements
[style + MEDIUM/LOW security findings, numbered]
## Verdict: PASS | PASS WITH NOTES | NEEDS REVISION

For a project review, one section per file then:
## Overall Project Verdict
[2-3 sentences]
PASS | PASS WITH NOTES | NEEDS REVISION

After writing the report, call save_review_to_file with the full report text.
Then output exactly: REVIEW COMPLETE
Only speak after all three specialist agents have contributed.
```

## Tool: save_review_to_file
- `save_review_to_file(report: str) -> str`
- Writes to `review_output.md` in CWD (always overwrites)
- Prepends `# CodeSentinel Review Report\n\n`
- Fixed path only — never accept dynamic paths from agent output

## Speaker Selection
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
- Agent factory functions: `create_<agent_name>()`, return agent instance
- All imports: absolute paths from project root
- System prompts: assign to variable first, then pass to agent
- `review_output.md`: always overwritten on each run
- Flask app runs with `debug=False` in production, `debug=True` for development
- Never expose Python tracebacks in HTTP responses

## Do Not
- Do not hardcode language-specific rules in agent prompts
- Do not restrict language detection to a fixed list
- Do not use `speaker_selection_method="round_robin"`
- Do not add retry logic to LLM calls
- Do not use `subprocess`, `os.system`, or shell execution
- Do not review config/data files (`.json`, `.yaml`, `.env`, `.xml`, `.csv`, `.md`)
- Do not follow symlinks when scanning directories
- Do not store uploaded files permanently — use `tempfile` and delete after review
- Do not expose internal file paths or server details in API responses
