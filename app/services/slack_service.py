import logging

import anthropic
from flask import current_app

logger = logging.getLogger(__name__)

NOTIFY_MODEL = "claude-haiku-4-5-20251001"


def _mcp_kwargs() -> dict:
    mcp_server = {
        "type": "url",
        "url": current_app.config["SLACK_MCP_URL"],
        "name": "slack",
        "authorization_token": current_app.config["SLACK_TOKEN"],
    }
    mcp_toolset = {"type": "mcp_toolset", "mcp_server_name": "slack"}
    return {
        "extra_body": {"mcp_servers": [mcp_server], "tools": [mcp_toolset]},
        "extra_headers": {"anthropic-beta": "mcp-client-2025-11-20"},
    }


def send_dm(user_id: str, text: str) -> bool:
    """Send a Slack DM to a user via the Slack MCP connector.

    Uses a small Claude call with the Slack MCP toolset to open a DM and post
    the message verbatim. Returns True on success, False on failure.
    """
    if not user_id:
        logger.warning("send_dm: empty user_id; skipping.")
        return False
    if not current_app.config.get("SLACK_TOKEN"):
        logger.warning("send_dm: SLACK_TOKEN not configured; skipping.")
        return False

    client = anthropic.Anthropic(api_key=current_app.config["ANTHROPIC_API_KEY"])
    prompt = (
        f"Post a direct message to the Slack user with ID {user_id}. "
        "You MUST use the Slack MCP tools to actually send the message — do not just reply with text. "
        "Typical flow: call the Slack MCP tool that opens or retrieves a DM conversation with that user ID, "
        "then call the tool that posts a message to that conversation. "
        "The message text to post, verbatim (do not paraphrase, translate, summarize, or add any commentary):\n\n"
        f"---\n{text}\n---\n\n"
        "After you have actually posted the message via an MCP tool call, reply with the single word: sent"
    )
    try:
        message = client.messages.create(
            model=NOTIFY_MODEL,
            max_tokens=2048,
            system="You are a reliable messaging relay. Always deliver messages by invoking the Slack MCP tools — never just acknowledge in text without calling a tool.",
            messages=[{"role": "user", "content": prompt}],
            **_mcp_kwargs(),
        )
    except Exception:
        logger.exception("Slack DM relay raised for user %s", user_id)
        return False

    block_types = [getattr(b, "type", "?") for b in message.content]
    tool_calls = [b for b in message.content if getattr(b, "type", "") in ("tool_use", "mcp_tool_use")]
    text_reply = " | ".join(
        getattr(b, "text", "") for b in message.content if getattr(b, "type", None) == "text"
    ).strip()

    logger.info(
        "Slack DM relay to %s: stop_reason=%s blocks=%s tool_calls=%d text=%r",
        user_id, message.stop_reason, block_types, len(tool_calls), text_reply[:500],
    )

    if not tool_calls:
        logger.error(
            "Slack DM relay to %s invoked no MCP tools — message was NOT delivered. "
            "model reply=%r blocks=%s",
            user_id, text_reply[:500], block_types,
        )
        return False
    return True
