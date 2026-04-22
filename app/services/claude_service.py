import base64
import json
import logging
import re

import anthropic
from flask import current_app

logger = logging.getLogger(__name__)


def extract_from_pdf(pdf_bytes: bytes, config: dict) -> dict:
    """Send PDF to Claude and return extracted fields as a dict."""
    client = anthropic.Anthropic(api_key=current_app.config["ANTHROPIC_API_KEY"])

    fields_description = "\n".join(
        f'- "{key}": {desc}' for key, desc in config["fields"].items()
    )
    user_prompt = config["user_prompt_prefix"] + fields_description

    pdf_b64 = base64.standard_b64encode(pdf_bytes).decode("utf-8")

    message = client.messages.create(
        model=config["model"],
        max_tokens=2048,
        system=config["system_prompt"],
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": "application/pdf",
                            "data": pdf_b64,
                        },
                    },
                    {"type": "text", "text": user_prompt},
                ],
            }
        ],
    )

    return _parse_json_response(message.content[0].text)


def extract_from_canvas(canvas_text: str, config: dict) -> dict:
    """Send canvas markdown to Claude and return extracted fields as a dict."""
    client = anthropic.Anthropic(api_key=current_app.config["ANTHROPIC_API_KEY"])

    fields_description = "\n".join(
        f'- "{key}": {desc}' for key, desc in config["fields"].items()
    )
    user_prompt = (
        config["user_prompt_prefix"]
        + fields_description
        + "\n\n--- CANVAS CONTENT ---\n"
        + canvas_text
    )

    message = client.messages.create(
        model=config["model"],
        max_tokens=4096,
        system=config["system_prompt"],
        messages=[{"role": "user", "content": user_prompt}],
    )

    return _parse_json_response(message.content[0].text)


def extract_from_canvas_url(canvas_url: str, config: dict) -> dict:
    """Use Slack MCP to fetch a canvas by URL, then extract fields into a dict."""
    client = anthropic.Anthropic(api_key=current_app.config["ANTHROPIC_API_KEY"])

    fields_description = "\n".join(
        f'- "{key}": {desc}' for key, desc in config["fields"].items()
    )
    user_prompt = (
        f"Use the Slack MCP tools to read the full content of the canvas at: {canvas_url}\n\n"
        "Then extract the fields below from the canvas content and return the JSON object.\n\n"
        + config["user_prompt_prefix"]
        + fields_description
    )

    mcp_server = {
        "type": "url",
        "url": current_app.config["SLACK_MCP_URL"],
        "name": "slack",
        "authorization_token": current_app.config["SLACK_TOKEN"],
    }
    mcp_toolset = {"type": "mcp_toolset", "mcp_server_name": "slack"}

    message = client.messages.create(
        model=config["model"],
        max_tokens=8192,
        system=config["system_prompt"],
        messages=[{"role": "user", "content": user_prompt}],
        extra_body={"mcp_servers": [mcp_server], "tools": [mcp_toolset]},
        extra_headers={"anthropic-beta": "mcp-client-2025-11-20"},
    )

    text_blocks = [b.text for b in message.content if getattr(b, "type", None) == "text"]
    combined = "\n".join(text_blocks).strip()

    if not combined:
        block_types = [getattr(b, "type", "?") for b in message.content]
        logger.error(
            "Canvas MCP call returned no text content. stop_reason=%s block_types=%s",
            message.stop_reason, block_types,
        )
        raise RuntimeError(
            f"Claude returned no text (stop_reason={message.stop_reason}, blocks={block_types})"
        )

    try:
        return _parse_json_response(combined)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", combined, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        logger.error(
            "Could not parse JSON from canvas MCP response. stop_reason=%s raw=%r",
            message.stop_reason, combined[:2000],
        )
        raise


def _parse_json_response(raw: str) -> dict:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw)
