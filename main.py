import argparse
import sys
import autogen
import autogen as ag2

from utils.input_handler import handle_inline, handle_file, handle_project
from utils.llm_config import LLM_CONFIG
from agents.bug_detector import create_bug_detector
from agents.style_checker import create_style_checker
from agents.security_auditor import create_security_auditor
from agents.summarizer import create_summarizer
from agents.user_proxy import create_user_proxy, create_spec_proxy
from tools.save_report import save_review_to_file


def parse_args():
    parser = argparse.ArgumentParser(description="CodeSentinel — AI-powered multi-agent code review")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--inline", action="store_true", help="Paste code inline in the terminal")
    group.add_argument("--file", metavar="PATH", help="Review a single source file")
    group.add_argument("--project", metavar="DIR", help="Review an entire project directory")
    return parser.parse_args()


def make_review_message(filepath, content, language):
    return (
        f"Please review the following {language} code from '{filepath}':\n\n"
        f"```\n{content}\n```"
    )


def speaker_selection_func(last_speaker, groupchat):
    """Enforce strict agent execution order with tool-call round-trip handling."""
    name = last_speaker.name
    agents = {a.name: a for a in groupchat.agents}
    messages = groupchat.messages

    if name == "Summarizer":
        last_msg = messages[-1] if messages else {}
        # Summarizer made a tool call — route to User_Proxy to execute it
        if last_msg.get("tool_calls") or last_msg.get("function_call"):
            return agents["User_Proxy"]
        # Summarizer has finalised (after seeing the tool result) — end chat
        return None

    if name == "User_Proxy":
        # If Summarizer has already spoken, this must be a tool execution result
        if any(m.get("name") == "Summarizer" for m in messages):
            return agents["Summarizer"]
        # Initial review request — start the specialist pipeline
        return agents["Bug_Detector"]

    order = ["User_Proxy", "Bug_Detector", "Style_Checker", "Security_Auditor", "Summarizer"]
    if name in order[:-1]:
        return agents[order[order.index(name) + 1]]
    return None


def run_single_review(filepath, content, language, user_proxy, bug_detector,
                      style_checker, security_auditor, summarizer):
    """Run the full 5-agent GroupChat for a single file or inline snippet."""
    print(f"\n[Starting review of '{filepath}' ({language})]\n")

    groupchat = autogen.GroupChat(
        agents=[user_proxy, bug_detector, style_checker, security_auditor, summarizer],
        messages=[],
        speaker_selection_method=speaker_selection_func,
        max_round=10,
    )
    manager = autogen.GroupChatManager(groupchat=groupchat, llm_config=LLM_CONFIG)

    message = make_review_message(filepath, content, language)
    user_proxy.initiate_chat(manager, message=message)


def run_project_mode(files, user_proxy, summarizer):
    """
    Project mode:
      1. For each file: run Bug_Detector, Style_Checker, Security_Auditor via 2-agent chats.
      2. After all files: run Summarizer once with all combined findings.
    """
    n = len(files)
    all_findings = []

    for i, (filepath, content, language) in enumerate(files):
        print(f"\n[Reviewing file {i + 1}/{n}: {filepath}]")
        code_msg = make_review_message(filepath, content, language)

        # Fresh specialist agents and proxy for each file to avoid history contamination
        spec_proxy = create_spec_proxy()
        bug_detector = create_bug_detector()
        style_checker = create_style_checker()
        security_auditor = create_security_auditor()

        print("  [Bug_Detector running...]")
        bug_result = spec_proxy.initiate_chat(bug_detector, message=code_msg, max_turns=2, silent=True)
        bug_findings = (
            bug_result.chat_history[-1]["content"]
            if bug_result.chat_history
            else "No bugs found."
        )

        print("  [Style_Checker running...]")
        spec_proxy2 = create_spec_proxy()
        style_result = spec_proxy2.initiate_chat(style_checker, message=code_msg, max_turns=2, silent=True)
        style_findings = (
            style_result.chat_history[-1]["content"]
            if style_result.chat_history
            else "No style issues found."
        )

        print("  [Security_Auditor running...]")
        spec_proxy3 = create_spec_proxy()
        sec_result = spec_proxy3.initiate_chat(security_auditor, message=code_msg, max_turns=2, silent=True)
        security_findings = (
            sec_result.chat_history[-1]["content"]
            if sec_result.chat_history
            else "No security issues found."
        )

        all_findings.append({
            "filepath": filepath,
            "language": language,
            "bugs": bug_findings,
            "style": style_findings,
            "security": security_findings,
        })

    # Build combined findings message for Summarizer
    parts = [f"Please produce a combined project review report for the following {n} file(s).\n"]
    for idx, f in enumerate(all_findings):
        parts.append(f"\n=== File {idx + 1}/{n}: {f['filepath']} ({f['language']}) ===\n")
        parts.append(f"Bug_Detector findings:\n{f['bugs']}\n\n")
        parts.append(f"Style_Checker findings:\n{f['style']}\n\n")
        parts.append(f"Security_Auditor findings:\n{f['security']}\n")
    combined = "".join(parts)

    print("\n[Generating combined project report...]\n")

    def project_summary_speaker_selection(last_speaker, groupchat):
        agents = {a.name: a for a in groupchat.agents}
        messages = groupchat.messages
        name = last_speaker.name

        if name == "Summarizer":
            last_msg = messages[-1] if messages else {}
            # Summarizer made a tool call — route to User_Proxy to execute it
            if last_msg.get("tool_calls") or last_msg.get("function_call"):
                return agents["User_Proxy"]
            return None

        # User_Proxy always routes to Summarizer (initial message or tool result)
        return agents["Summarizer"]

    groupchat = autogen.GroupChat(
        agents=[user_proxy, summarizer],
        messages=[],
        speaker_selection_method=project_summary_speaker_selection,
        max_round=4,
    )
    manager = autogen.GroupChatManager(groupchat=groupchat, llm_config=LLM_CONFIG)
    user_proxy.initiate_chat(manager, message=combined)


def main():
    args = parse_args()

    # Resolve input to list of (filepath, content, language)
    if args.inline:
        files = handle_inline()
    elif args.file:
        files = handle_file(args.file)
    else:
        files = handle_project(args.project)

    # Create core agents
    print("[Initializing CodeSentinel agents...]")
    user_proxy = create_user_proxy()
    summarizer = create_summarizer()

    # Register save_review_to_file: Summarizer calls it, User_Proxy executes it
    ag2.register_function(
        save_review_to_file,
        caller=summarizer,
        executor=user_proxy,
        name="save_review_to_file",
        description="Save the complete code review report to review_output.md",
    )

    if args.project:
        run_project_mode(files, user_proxy, summarizer)
    else:
        bug_detector = create_bug_detector()
        style_checker = create_style_checker()
        security_auditor = create_security_auditor()
        filepath, content, language = files[0]
        run_single_review(
            filepath, content, language,
            user_proxy, bug_detector, style_checker, security_auditor, summarizer,
        )

    print("\n[Review complete. Report saved to review_output.md]")


if __name__ == "__main__":
    main()
