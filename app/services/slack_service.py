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
        f"Send a direct message to the Slack user with ID {user_id}. "
        "Use the Slack MCP tools to open a DM conversation with that user and post the message. "
        "The message text to post, verbatim (do not paraphrase, translate, summarize, or add any commentary):\n\n"
        f"---\n{text}\n---\n\n"
        "After the message is posted, reply with the single word: sent"
    )
    try:
        message = client.messages.create(
            model=NOTIFY_MODEL,
            max_tokens=1024,
            system="You are a reliable messaging relay. Use the Slack MCP tools to deliver exact messages to specified user IDs.",
            messages=[{"role": "user", "content": prompt}],
            **_mcp_kwargs(),
        )
        logger.info(
            "Slack DM relay to %s: stop_reason=%s blocks=%s",
            user_id,
            message.stop_reason,
            [getattr(b, "type", "?") for b in message.content],
        )
        return True
    except Exception:
        logger.exception("Slack DM relay failed for user %s", user_id)
        return False
