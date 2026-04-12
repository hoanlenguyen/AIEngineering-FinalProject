import autogen


def create_user_proxy():
    """UserProxyAgent that initiates chats and executes tool calls on behalf of Summarizer."""
    return autogen.UserProxyAgent(
        name="User_Proxy",
        human_input_mode="NEVER",
        code_execution_config=False,
        is_termination_msg=lambda msg: "REVIEW COMPLETE" in (msg.get("content") or ""),
    )


def create_spec_proxy():
    """Lightweight UserProxyAgent for per-file specialist runs in project mode."""
    return autogen.UserProxyAgent(
        name="Spec_Proxy",
        human_input_mode="NEVER",
        code_execution_config=False,
        is_termination_msg=lambda msg: False,
    )
