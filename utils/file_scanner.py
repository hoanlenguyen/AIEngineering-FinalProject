import os
from utils.language_detector import COMMON_EXTENSIONS, detect_language

SKIP_EXTENSIONS = {
    ".json", ".yaml", ".yml", ".toml", ".env", ".xml",
    ".md", ".txt", ".lock", ".csv",
}

SKIP_DIRS = {
    "node_modules", "__pycache__", ".git", "venv", ".venv", "env",
    "dist", "build", "target", "bin", "obj", ".idea", ".vscode",
}

MAX_FILE_SIZE = 100 * 1024  # 100 KB
MAX_FILES = 20


def scan_project(directory):
    """
    Recursively scan directory for reviewable source files.
    Returns (list of (relative_path, content, language), was_capped).
    was_capped is True if more than MAX_FILES files were found.
    """
    results = []
    directory = os.path.abspath(directory)
    capped = False

    for root, dirs, files in os.walk(directory, followlinks=False):
        # Prune skip directories in-place
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]

        for filename in sorted(files):
            filepath = os.path.join(root, filename)

            # Never follow symlinks
            if os.path.islink(filepath):
                continue

            ext = os.path.splitext(filename)[1].lower()

            # Skip non-code extensions
            if ext in SKIP_EXTENSIONS:
                continue

            # Skip files with no extension unless they're clearly code-like
            if not ext:
                continue

            # Skip files not in COMMON_EXTENSIONS unless they have a code-like extension
            if ext not in COMMON_EXTENSIONS and not _is_code_like_ext(ext):
                continue

            # Skip files over 100 KB
            try:
                if os.path.getsize(filepath) > MAX_FILE_SIZE:
                    continue
            except OSError:
                continue

            # Read content
            try:
                with open(filepath, encoding="utf-8") as f:
                    content = f.read()
            except (OSError, UnicodeDecodeError):
                continue

            language = detect_language(code=content, ext=ext)
            relative_path = os.path.relpath(filepath, directory)
            results.append((relative_path, content, language))

            if len(results) >= MAX_FILES:
                capped = True
                return results, capped

    return results, capped


def _is_code_like_ext(ext):
    """Accept any non-empty extension not in skip list as potentially code."""
    return bool(ext) and ext not in SKIP_EXTENSIONS
