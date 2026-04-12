def save_review_to_file(report: str) -> str:
    """Write the review report to review_output.md in the current working directory."""
    output_path = "review_output.md"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# CodeSentinel Review Report\n\n")
        f.write(report)
    return "Report saved to review_output.md"
