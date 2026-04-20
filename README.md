# Final Project Report — AI Engineering (IC00BD87-3001)

**Course:** AI Engineering (IC00BD87-3001)
**Student name(s) + Student IDs:** 
---
Hoan Le
Hoan.Le@student.oulu.fi
Student number: 2504960 
---
Khoa Dinh
t0dida00@students.oamk.fi
Student number: 2508783 
---
Van Nguyen
Van.M.Nguyen@student.oulu.fi
Student number: 2506205

## 1. Project Name

**CodeSentinel** — A Multi-Agent, Multi-Language Code Review Assistant with Web UI
Project link: 
https://github.com/hoanlenguyen/AIEngineering-FinalProject
---

## 2. How to Run the Project

### Prerequisites
- Python 3.10+
- Install dependencies:
  ```
  pip install ag2 openai flask
  ```

### Run the Web UI (recommended)
```
python app.py
```
Then open `http://localhost:5000` in your browser. The UI provides three input modes via tabs:
- **Inline** — paste code directly into the textarea
- **File** — upload a source file from your machine
- **Project** — enter a local folder path to review an entire project

The review runs automatically, progress is shown in real time, and the final report is rendered in the browser. A **Download Report** button saves `review_output.md` to your machine.

### Run the CLI (alternative, no browser needed)
```
# Single file
python main.py --file path/to/your_code.py

# Paste inline
python main.py --inline

# Entire project
python main.py --project path/to/your_project/
```

No API key is needed — the system uses the provided AWS proxy:
`https://5f5832nb90.execute-api.eu-central-1.amazonaws.com/v1`

Model used: `openai/gpt-4.1-mini`

---

## Test Files

The `tests/` directory contains sample code files with intentional bugs, style issues, and security vulnerabilities for testing the system across multiple languages.

### Available Test Files

| File | Language | Issues Included |
|---|---|---|
| **test_sample.py** | Python | `eval()` with user input (HIGH security), hardcoded credentials, SQL injection, resource leak (unclosed file), ZeroDivisionError, PEP 8 violations |
| **test_sample.js** | JavaScript | XSS via `innerHTML` (HIGH security), hardcoded API key, synchronous XHR, off-by-one array access, loose equality (`==` vs `===`), unused variables |
| **TestSample.java** | Java | SQL injection via string concatenation (HIGH security), hardcoded password, silent exception catch, DivideByZeroException, resource leak, missing Javadoc |
| **TestSample.cs** | C# | SQL injection (HIGH security), hardcoded credentials, DivideByZeroException, IndexOutOfRangeException (off-by-one), camelCase method names, missing spaces |

### Quick Test Commands

**Test a single file (file mode):**
```bash
python app.py
# Then upload tests/test_sample.py via the File tab

# Or via CLI:
python main.py --file tests/test_sample.py
```

**Test all samples (project mode):**
```bash
python app.py
# Then enter tests/ as the project path in the Project tab

# Or via CLI:
python main.py --project tests/
```

**Expected Results**

All test files contain intentional HIGH-severity security issues and bugs that CodeSentinel should detect:
- **test_sample.py**: Detects `eval()` usage, hardcoded secrets
- **test_sample.js**: Detects XSS vulnerability, hardcoded API key
- **TestSample.java**: Detects SQL injection, hardcoded password
- **TestSample.cs**: Detects SQL injection, hardcoded credentials

Verdict for all files: **NEEDS REVISION** (due to HIGH-severity findings)

---

## 3. System Purpose / Primary Goal

CodeSentinel is a multi-agent system that performs automated code review on source code written in any programming language. It accepts input as a pasted snippet, a single source file, or an entire project directory — via a web browser UI or a command-line interface. The system detects the programming language automatically, routes code through three specialist review agents, and presents the findings as a structured, colour-coded report.

The primary goal is to help developers and students quickly identify bugs, style violations, and security issues across a wide range of languages and input types — without needing language-specific configuration, tool setup, or command-line experience.

---

## 4. System Boundaries (In Scope / Out of Scope)

### In Scope
- Code review for any programming language the underlying LLM has knowledge of
- Three input modes: inline snippet, single file upload, project directory path
- Real-time agent progress display in the browser via Server-Sent Events
- Bug detection, style analysis, and security auditing per file
- Automatic language detection from file extension and/or LLM inference
- Manual language override via dropdown in the UI
- Project-level combined report with per-file sections and an overall verdict
- Colour-coded verdict badge (PASS / PASS WITH NOTES / NEEDS REVISION)
- Downloadable markdown report
- CLI interface for non-browser use
- Multi-agent orchestration using AG2 GroupChat

### Out of Scope
- Languages the LLM has no training knowledge of (review quality not guaranteed)
- Automatic code fixing or patching
- User accounts, authentication, or saved review history
- Deployment to a public server (designed for localhost use)
- Integration with GitHub, GitLab, or CI/CD pipelines
- Projects larger than 20 files (capped with a warning)
- Files larger than 100 KB (skipped as likely generated or minified)
- Runtime execution of submitted code

### Non-Goals
- The system should **not** execute or run user-provided code under any circumstances
- The system should **not** make architectural design recommendations
- The system should **not** rewrite or auto-correct code on behalf of the user

---

## 5. Top-Level Tasks the System Must Accomplish

- Serve a web UI at `localhost:5000` with three input tabs (Inline, File, Project)
- Accept code input via UI or CLI and resolve it to one or more `(filepath, content, language)` tuples
- For project mode: scan the directory, skip non-code and oversized files, cap at 20 files
- Detect programming language from file extension hint and LLM inference; allow manual override
- Stream real-time agent progress to the browser via Server-Sent Events
- **Bug Detector Agent:** Identify bugs using language-appropriate best practices
- **Style Checker Agent:** Flag violations of the relevant style guide for the detected language
- **Security Auditor Agent:** Identify OWASP-relevant vulnerabilities with HIGH/MEDIUM/LOW labels
- **Summarizer Agent:** Aggregate findings, produce a structured report, call `save_review_to_file`
- Return the rendered report to the browser with a colour-coded verdict badge
- Save the final report to `review_output.md` and offer it as a download

---

## 6. Is There a Human in the Loop?

**Yes — Human interaction via the UI.**

The human provides the input (code snippet, file upload, or folder path) through the browser interface and can optionally override the detected language. Once the review is submitted, the system runs fully automatically. The human reads the rendered report and acts on the findings. There is no approval or intervention step within the agent pipeline itself.

---

## 7. Success Criteria

### Evaluation Plan

| Test Scenario | Input Mode | Expected Outcome |
|---|---|---|
| Python snippet with eval() and PEP 8 errors | UI — Inline | All issues detected, report rendered in browser |
| JavaScript file with innerHTML injection | UI — File upload | Security finding with HIGH severity, red verdict badge |
| Java file with SQL concatenation bug | UI — File upload | Bug + security findings, NEEDS REVISION verdict |
| Go file with clean idiomatic code | CLI — file | No critical issues, PASS verdict |
| Mixed project (py + js + java files) | UI — Project path | Per-file sections, combined verdict, downloadable report |

| Metric | Measurement | Target |
|---|---|---|
| UI loads correctly | Browser renders all three tabs without errors | 100% |
| Language detection accuracy | Correct language / total inputs | ≥ 95% for common languages |
| SSE progress updates | All 5 steps shown correctly during review | 100% |
| Bug detection rate | % of planted bugs correctly found | ≥ 70% |
| Style detection rate | % of style violations flagged | ≥ 70% |
| Security detection rate | % of known vulnerabilities found | ≥ 70% |
| False positive rate | Findings flagged that are not real issues | ≤ 2 per file |
| Report rendered correctly | Markdown renders without broken layout | 100% |
| Download works | `review_output.md` downloads with correct content | 100% |
| Report quality | Human rating (1–5) for clarity and usefulness | ≥ 4/5 |

---

## 8. External Data Used

- None. The system uses only the code provided at runtime as input.
- The LLMs accessed via OpenRouter through the AWS proxy serve as the knowledge base for language-specific conventions, style guides, and vulnerability patterns.
- `marked.js` (loaded from CDN) is used client-side to render markdown — no data is sent to it.

---

## 9. Multi-Agent Orchestration Pattern

**AG2 GroupChat with Custom Speaker Selection Function (Orchestrator Pattern)**

The system uses AG2's `GroupChat` with a custom `speaker_selection_func` to enforce a strict agent execution order. When a review is submitted (via UI or CLI):

1. The **UserProxy** agent initiates the group chat with the code snippet and detected language.
2. The **Bug Detector**, **Style Checker**, and **Security Auditor** agents speak in sequence.
3. The custom speaker selection function ensures **Summarizer** only speaks after all three.
4. The **Summarizer** calls `save_review_to_file`, saves the report, outputs `REVIEW COMPLETE`.

For project mode, specialist agents loop over each file; Summarizer runs once at the end.

The Flask UI runs the agent GroupChat in a **background thread** so the browser stays responsive. A shared `queue.Queue` passes progress events from the agent thread to the SSE endpoint, which streams them to the browser.

### Agent Table

| Agent | Purpose / Responsibility | Inputs | Success / Stop Criteria | Capabilities and Tools | External Knowledge (e.g. RAG)? | Memory? | Guardrails? |
|---|---|---|---|---|---|---|---|
| User_Proxy | Initiates group chat, passes code and language to agents, executes tool calls on behalf of Summarizer | Code snippet + detected language label | Chat ends after Summarizer saves report and outputs REVIEW COMPLETE | Executes `save_review_to_file` tool | No | No | Never executes submitted code; `code_execution_config=False` |
| Bug_Detector | Identifies logical errors, runtime exceptions, null dereferences, type mismatches, and language-specific bugs | Code snippet + language tag | Numbered findings list, or "No bugs found." | LLM inference (language-agnostic) | No | No | Does not execute code or suggest fixes |
| Style_Checker | Flags violations of the standard or widely accepted style guide for the detected language | Code snippet + language tag | Numbered style issues list, or "No style issues found." | LLM inference (language-agnostic) | No | No | Applies conventions for detected language only; no opinionated rewriting |
| Security_Auditor | Identifies OWASP-relevant vulnerabilities and language-specific security risks with severity labels | Code snippet + language tag | Numbered findings with HIGH/MEDIUM/LOW, or "No security issues found." | LLM inference (language-agnostic) | No | No | Does not suggest exploit code; severity labels required per finding |
| Summarizer | Aggregates all specialist findings into a structured report and saves it to disk via tool call | Findings from all three specialists | Report saved; outputs "REVIEW COMPLETE" to end chat | Calls `save_review_to_file` (caller) | No | No | Speaks only after all three specialists; fixed output path for file write |

---

## 10. Justification of Orchestration Pattern

AG2's GroupChat with a custom speaker selection function was chosen for the following reasons:

**1. Strict ordering without manual chaining.** The custom `speaker_selection_func` enforces that the Summarizer speaks only after all three specialists have contributed, cleanly and without hardcoded chaining logic.

**2. Separation of concerns.** Each specialist focuses on one review dimension. This reduces prompt complexity and produces higher-quality, more focused outputs than a single "do everything" agent.

**3. Language-agnostic prompting.** Each agent receives the detected language as context and applies the LLM's own knowledge of that language's best practices. The same agents handle Python, Go, Rust, and any other language without maintaining hardcoded rule tables.

**4. Background thread compatibility.** Because AG2's GroupChat is self-contained and returns after `REVIEW COMPLETE`, it runs cleanly in a Flask background thread. Progress events are emitted to a shared queue without modifying the agent architecture.

**5. Natural scalability to project mode.** Stateless specialist agents loop over files with no redesign; only the Summarizer's input changes for project reviews.

**6. Tool call integration.** Assigning `save_review_to_file` to the Summarizer (with UserProxy as executor) is idiomatic AG2 and satisfies the assignment's tool call requirement in a motivated way — saving the report is the natural final step.

A reflection or debate pattern was considered but rejected — code review sub-tasks are independent and do not require agents to critique each other's output.

---

## 11. Safety and Security Concerns

| Concern | How It Was Addressed |
|---|---|
| **Prompt injection via malicious code input** | Code is passed as text content only. No agent is instructed to execute or interpret it. `code_execution_config=False` on UserProxy. |
| **Malicious project paths (UI)** | Server validates path exists with `os.path.isdir` before scanning. Scanner uses `os.path.abspath`, does not follow symlinks, and only reads approved extensions. |
| **Uploaded file handling** | Files are saved to `tempfile.NamedTemporaryFile` and deleted immediately after the review completes. File contents are never stored permanently. |
| **Internal path exposure** | API responses never include server-side absolute paths or Python tracebacks. Errors return generic messages. |
| **Hallucinated vulnerabilities** | Summarizer is prompted to flag low-confidence findings as "unverified" in the report. |
| **Language misdetection** | Extension used as strong hint; LLM confirms. UI offers manual override dropdown. If UNKNOWN, an HTTP 400 error is returned with a clear message. |
| **Large project handling** | Capped at 20 files with a user warning to prevent excessive token use or long-running reviews. |
| **API proxy misuse** | No API key stored in codebase. Proxy URL is the only endpoint. |
| **File write safety** | `save_review_to_file` writes only to fixed path `review_output.md`; never accepts dynamic paths from agent output. |
| **Over-reliance on the system** | Report footer includes a disclaimer to verify findings with a human developer before acting. |

---

## Declaration of Use of AI

- **Code:** GitHub Copilot was used for boilerplate and autocomplete. Claude (claude.ai) was used to generate initial agent system prompt templates, the Flask route structure, and the `CLAUDE.md` project instruction file — all manually reviewed and refined.
- **Report:** This report was drafted with assistance from Claude (claude.ai) based on project description, architecture decisions, and the course-provided template. All content was reviewed and edited by the student.
