# Final Project Report — AI Engineering (IC00BD87-3001)

**Course:** AI Engineering (IC00BD87-3001)
**Student name(s) + Student IDs:** *(fill in)*

---

## 1. Project Name

**CodeSentinel** — A Multi-Agent, Multi-Language Code Review Assistant

---

## 2. How to Run the Project

### Prerequisites
- Python 3.10+
- Install dependencies:
  ```
  pip install ag2 openai
  ```

### Three input modes

**Mode 1 — Inline snippet** (paste code directly in the terminal):
```
python main.py --inline
```
Paste your code and type `END` on a new line to submit.

**Mode 2 — Single file** (review one source file):
```
python main.py --file path/to/your_code.py
```
Supports any source code file. Language is detected automatically from the file extension and content.

**Mode 3 — Project directory** (review an entire local project):
```
python main.py --project path/to/your_project/
```
The system scans the directory recursively, detects all source files (up to 20), reviews each one, and produces a single combined report.

The final report is always saved to `review_output.md` in the current working directory.

No API key is needed — the system uses the provided AWS proxy:
`https://5f5832nb90.execute-api.eu-central-1.amazonaws.com/v1`

Model used: `openai/gpt-4.1-mini`

---

## 3. System Purpose / Primary Goal

CodeSentinel is a multi-agent system that performs automated code review on source code written in any programming language. It accepts input as a pasted snippet, a single source file, or an entire project directory. The system detects the programming language automatically, routes code through three specialist review agents, and synthesizes their findings into a structured report saved to disk.

The primary goal is to help developers and students quickly identify bugs, style violations, and security issues across a wide range of languages and input types — without needing language-specific configuration or tool setup.

---

## 4. System Boundaries (In Scope / Out of Scope)

### In Scope
- Code review for any programming language the underlying LLM has knowledge of
  (e.g. Python, JavaScript, TypeScript, Java, C#, Go, Rust, Ruby, PHP, Kotlin, Swift, C/C++, SQL, Shell, and more)
- Three input modes: inline snippet, single file, project directory
- Bug detection, style analysis, and security auditing per file
- Automatic language detection from file extension and/or LLM inference
- Project-level combined report with per-file sections and an overall verdict
- Multi-agent orchestration using AG2 GroupChat

### Out of Scope
- Languages the LLM has no training knowledge of (review quality not guaranteed)
- Automatic code fixing or patching
- Integration with GitHub, GitLab, or CI/CD pipelines
- Projects larger than 20 files (capped with a warning)
- Files larger than 100 KB (skipped as likely generated or minified)
- Config and data files (`.json`, `.yaml`, `.env`, `.xml`, `.csv`, `.md`)
- Runtime execution of submitted code

### Non-Goals
- The system should **not** execute or run user-provided code under any circumstances
- The system should **not** make architectural design recommendations
- The system should **not** rewrite or auto-correct code on behalf of the user

---

## 5. Top-Level Tasks the System Must Accomplish

- Accept code input via one of three modes: `--inline`, `--file`, or `--project`
- Resolve input to one or more `(filepath, content, language)` tuples
- For `--project` mode: scan the directory, skip non-code and oversized files, cap at 20 files
- Detect programming language from file extension hint and LLM inference
- **Bug Detector Agent:** Identify bugs, runtime errors, and logic issues using language-appropriate best practices for the detected language
- **Style Checker Agent:** Flag violations of the standard or widely accepted style guide for the detected language
- **Security Auditor Agent:** Identify OWASP-relevant vulnerabilities and language-specific security risks, labelled HIGH/MEDIUM/LOW
- **Summarizer Agent:** Aggregate findings from all three specialists, produce a structured per-file or per-project report, and call `save_review_to_file` to persist the output
- Save the final report to `review_output.md`

---

## 6. Is There a Human in the Loop?

**Yes — minimally.**

The human provides the input at the start (code snippet, file path, or directory path). If the language cannot be detected automatically, the system prompts the user to specify it manually. Once input is resolved, the system runs fully automatically. The human reads and acts on the final saved report. There is no approval or intervention step within the agent pipeline itself.

---

## 7. Success Criteria

### Evaluation Plan

The system is evaluated on five test scenarios covering all three input modes and a range of languages.

| Test Scenario | Input Mode | Expected Outcome |
|---|---|---|
| Python snippet with eval() and PEP 8 errors | --inline | All issues detected, report saved |
| JavaScript file with innerHTML injection | --file | Security finding with HIGH severity |
| Java file with SQL concatenation bug | --file | Bug + security findings, NEEDS REVISION verdict |
| Go file with clean idiomatic code | --file | No critical issues, PASS verdict |
| Mixed project (py + js + java files) | --project | Per-file sections, combined project verdict |

| Metric | Measurement | Target |
|---|---|---|
| Language detection accuracy | Correct language / total inputs | ≥ 95% for common languages |
| Bug detection rate | % of planted bugs correctly found | ≥ 70% |
| Style detection rate | % of style violations flagged | ≥ 70% |
| Security detection rate | % of known vulnerabilities found | ≥ 70% |
| False positive rate | Findings flagged that are not real issues | ≤ 2 per file |
| Project scan correctness | Correct files included / excluded | 100% |
| Report saved correctly | File exists and readable after each run | 100% |
| Report quality | Human rating (1–5) for clarity and usefulness | ≥ 4/5 |

---

## 8. External Data Used

- None. The system uses only the code provided at runtime as input.
- The LLMs accessed via OpenRouter through the AWS proxy serve as the knowledge base for language-specific conventions, style guides, and vulnerability patterns.

---

## 9. Multi-Agent Orchestration Pattern

**AG2 GroupChat with Custom Speaker Selection Function (Orchestrator Pattern)**

The system uses AG2's `GroupChat` with a custom `speaker_selection_func` to enforce a strict agent execution order:

1. The **UserProxy** agent initiates the group chat with a code snippet and its detected language.
2. The **Bug Detector**, **Style Checker**, and **Security Auditor** agents each speak in sequence, producing their analysis independently.
3. The custom speaker selection function ensures the **Summarizer** only speaks after all three specialists have contributed.
4. The **Summarizer** calls the `save_review_to_file` tool to persist the report, then terminates the chat with `REVIEW COMPLETE`.

For `--project` mode, the three specialist agents run once per file (collecting findings), and the Summarizer runs once at the end across all findings in a single combined project report.

### Agent Table

| Agent | Purpose / Responsibility | Inputs | Success / Stop Criteria | Capabilities and Tools | External Knowledge (e.g. RAG)? | Memory? | Guardrails? |
|---|---|---|---|---|---|---|---|
| User_Proxy | Initiates the group chat, passes code and language to agents, executes tool calls on behalf of Summarizer | Code snippet + detected language label | Chat terminates after Summarizer saves report and outputs REVIEW COMPLETE | Executes `save_review_to_file` tool | No | No | Never executes submitted code; `code_execution_config=False` |
| Bug_Detector | Identifies logical errors, runtime exceptions, null dereferences, type mismatches, and language-specific common bugs | Code snippet + language tag | Produces numbered list of findings, or "No bugs found." | LLM inference (language-agnostic) | No | No | Instructed not to execute code or suggest fixes |
| Style_Checker | Flags violations of the standard or widely accepted style guide for the detected language | Code snippet + language tag | Produces numbered list of style issues, or "No style issues found." | LLM inference (language-agnostic) | No | No | Applies conventions for the specified language only; no opinionated rewriting |
| Security_Auditor | Identifies OWASP-relevant vulnerabilities and language-specific security risks with severity labels | Code snippet + language tag | Produces numbered list with HIGH/MEDIUM/LOW severity, or "No security issues found." | LLM inference (language-agnostic) | No | No | Does not suggest exploit code; severity labels required per finding |
| Summarizer | Aggregates all specialist findings into a structured report; saves report to disk via tool call | Findings from Bug_Detector, Style_Checker, Security_Auditor | Report saved successfully; outputs "REVIEW COMPLETE" to end the chat | Calls `save_review_to_file` (caller) | No | No | Speaks only after all three specialists; fixed output path for file write |

---

## 10. Justification of Orchestration Pattern

AG2's GroupChat with a custom speaker selection function was chosen for the following reasons:

**1. Strict ordering without manual chaining.** The custom `speaker_selection_func` enforces that the Summarizer speaks only after all three specialists have contributed. This is cleaner than manually chaining function calls and more readable than a hardcoded round-robin schedule.

**2. Separation of concerns.** Each specialist agent focuses on exactly one review dimension. This reduces prompt complexity and produces higher-quality, more focused outputs compared to a single "do everything" agent.

**3. Language-agnostic prompting.** Each agent receives the detected language as context and applies best practices for that language based on the LLM's own knowledge. This means the system works for any language without maintaining hardcoded rule tables — a Go file is reviewed by Go conventions, a Rust file by Rust conventions, and so on.

**4. Natural scalability to project mode.** Because the specialist agents are stateless and receive only the current file as input, the same GroupChat can be looped over multiple files. Only the Summarizer's input changes — it receives all per-file findings combined. No redesign is needed to support `--project` mode.

**5. Tool call integration.** AG2's GroupChat natively supports tool-calling agents. Assigning `save_review_to_file` to the Summarizer (with UserProxy as executor) follows idiomatic AG2 patterns and satisfies the assignment's tool call requirement in a natural, motivated way.

**6. Extensibility.** Adding a new specialist agent (e.g., a Performance Advisor) requires only inserting it into the group and updating the speaker selection logic — no restructuring of the pipeline is needed.

A reflection or debate pattern was considered but rejected, as code review sub-tasks (bugs, style, security) are independent — agents do not need to critique each other's output.

---

## 11. Safety and Security Concerns

| Concern | How It Was Addressed |
|---|---|
| **Prompt injection via malicious code input** | Code is treated strictly as text content in the chat message. No agent is instructed to execute or interpret the code. `code_execution_config=False` is set on UserProxy. |
| **Malicious project paths** | `file_scanner.py` resolves paths with `os.path.abspath`, does not follow symlinks, and only reads files with known code extensions. Files over 100 KB are skipped. |
| **Hallucinated vulnerabilities (false positives)** | The Summarizer is prompted to include a confidence label per finding where uncertain. Low-confidence findings are marked as "unverified" in the report. |
| **Language misdetection** | File extension is used as a strong hint to the LLM detector. If language is UNKNOWN, the user is prompted to specify it manually before proceeding. |
| **Over-reliance on the system** | The report footer includes a disclaimer that findings should be verified by a human developer before acting on them. |
| **API proxy misuse** | No API key is stored in the codebase. The proxy URL is the only endpoint used, as provided by the course. |
| **File write safety** | `save_review_to_file` writes only to the fixed path `review_output.md` and never accepts dynamic file paths from agent output. |
| **Large project handling** | The system caps project scans at 20 files and warns the user if more are found, preventing excessively long chat sessions or token overuse. |

---

## Declaration of Use of AI

- **Code:** GitHub Copilot was used for boilerplate and autocomplete. Claude (claude.ai) was used to generate initial agent system prompt templates and the `CLAUDE.md` project instruction file, which were then manually reviewed and refined.
- **Report:** This report was drafted with assistance from Claude (claude.ai) based on a project description, architecture decisions, and the course-provided template. All content was reviewed and edited by the student.
