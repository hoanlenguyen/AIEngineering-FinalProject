import os
import sys
from utils.language_detector import detect_language
from utils.file_scanner import scan_project


def handle_inline():
    """Prompt user to paste code; return [(\'Inline snippet\', code, language)]."""
    print("Paste your code below. Type END on a new line when done:")
    lines = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line.strip() == "END":
            break
        lines.append(line)

    snippet = "\n".join(lines)
    if not snippet.strip():
        print("Error: No code was provided.")
        sys.exit(1)

    print("[Detecting language...]")
    language = detect_language(code=snippet, ext=None)
    if language == "UNKNOWN":
        language = input("Could not detect language. Please enter the language name: ").strip()

    return [("Inline snippet", snippet, language)]


def handle_file(path):
    """Read a single source file; return [(filename, content, language)]."""
    if not os.path.isfile(path):
        print(f"Error: File not found: {path}")
        sys.exit(1)

    ext = os.path.splitext(path)[1]
    try:
        with open(path, encoding="utf-8") as f:
            content = f.read()
    except (OSError, UnicodeDecodeError) as e:
        print(f"Error reading file: {e}")
        sys.exit(1)

    print("[Detecting language...]")
    language = detect_language(code=content, ext=ext)
    if language == "UNKNOWN":
        language = input("Could not detect language. Please enter the language name: ").strip()

    filename = os.path.basename(path)
    return [(filename, content, language)]


def handle_project(directory):
    """Scan a project directory; return list of (relative_path, content, language)."""
    if not os.path.isdir(directory):
        print(f"Error: Directory not found: {directory}")
        sys.exit(1)

    print("[Scanning project directory...]")
    files, was_capped = scan_project(directory)

    if was_capped:
        print("Warning: More than 20 files found. Only the first 20 will be reviewed.")

    if not files:
        print("No reviewable source files found in the project directory.")
        sys.exit(1)

    print(f"[Found {len(files)} file(s) to review]")
    return files
