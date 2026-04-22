import base64
import json
import logging
import re

import anthropic
from flask import current_app

logger = logging.getLogger(__name__)

MAX_REWRITE_RETRIES = 2


def _field_items(config: dict):
    """Yield (key, description, max_length or None) for each field.

    Supports two forms in config["fields"]:
      - "key": "description string"
      - "key": {"description": "...", "max_length": N}
    """
    for key, val in config["fields"].items():
        if isinstance(val, dict):
            yield key, val.get("description", ""), val.get("max_length")
        else:
            yield key, val, None


def _build_fields_description(config: dict) -> str:
    lines = []
    for key, desc, max_len in _field_items(config):
        if max_len:
            lines.append(f'- "{key}": {desc} (max {max_len} characters)')
        else:
            lines.append(f'- "{key}": {desc}')
    return "\n".join(lines)


def _max_lengths(config: dict) -> dict:
    return {key: ml for key, _, ml in _field_items(config) if ml}


def _overlong_fields(extracted: dict, max_lengths: dict) -> dict:
    over = {}
    for key, max_len in max_lengths.items():
        val = extracted.get(key)
        if isinstance(val, str) and len(val) > max_len:
            over[key] = max_len
    return over


def _build_rewrite_prompt(extracted: dict, over_fields: dict) -> str:
    lines = [
        "Some fields in your previous JSON response exceeded their maximum character length.",
        "Rewrite each overlong field to be more concise while preserving the core meaning. Do not truncate mid-word or mid-sentence — produce complete, polished copy that fits within the limit.",
        "Return a JSON object with exactly the keys listed below and no others. No markdown fences, no commentary.",
        "",
        "Fields to shorten:",
    ]
    for key, max_len in over_fields.items():
        current = extracted[key]
        lines.append(
            f'- "{key}" (max {max_len} chars, currently {len(current)} chars): {json.dumps(current)}'
        )
    return "\n".join(lines)


def _enforce_max_lengths(client, config: dict, extracted: dict) -> dict:
    """Run post-extraction rewrite loop for any fields exceeding max_length."""
    max_lengths = _max_lengths(config)
    if not max_lengths:
        return extracted

    for attempt in range(MAX_REWRITE_RETRIES):
        over = _overlong_fields(extracted, max_lengths)
        if not over:
            return extracted

        logger.info(
            "Rewrite attempt %d: %d overlong field(s): %s",
            attempt + 1, len(over),
            {k: f"{len(extracted[k])}/{max_lengths[k]}" for k in over},
        )

        rewrite_msg = client.messages.create(
            model=config["model"],
            max_tokens=2048,
            system=config["system_prompt"],
            messages=[{"role": "user", "content": _build_rewrite_prompt(extracted, over)}],
        )
        try:
            rewrites = _parse_message_json(rewrite_msg)
        except json.JSONDecodeError:
            logger.warning("Rewrite attempt %d: could not parse JSON; aborting retries.", attempt + 1)
            break

        for k, v in rewrites.items():
            if k in over and isinstance(v, str):
                extracted[k] = v

    still_over = _overlong_fields(extracted, max_lengths)
    if still_over:
        logger.warning(
            "Fields still exceed max_length after %d rewrite attempts: %s",
            MAX_REWRITE_RETRIES,
            {k: f"{len(extracted[k])}/{max_lengths[k]}" for k in still_over},
        )
    return extracted


def _parse_message_json(message) -> dict:
    """Extract and parse JSON from a Claude message response."""
    text_blocks = [b.text for b in message.content if getattr(b, "type", None) == "text"]
    combined = "\n".join(text_blocks).strip()

    if not combined:
        block_types = [getattr(b, "type", "?") for b in message.content]
        logger.error(
            "Message returned no text content. stop_reason=%s block_types=%s",
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
            "Could not parse JSON from message. stop_reason=%s raw=%r",
            message.stop_reason, combined[:2000],
        )
        raise


def extract_from_pdf(pdf_bytes: bytes, config: dict) -> dict:
    """Send PDF to Claude and return extracted fields as a dict."""
    client = anthropic.Anthropic(api_key=current_app.config["ANTHROPIC_API_KEY"])

    fields_description = _build_fields_description(config)
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

    extracted = _parse_json_response(message.content[0].text)
    return _enforce_max_lengths(client, config, extracted)


def extract_from_canvas(canvas_text: str, config: dict) -> dict:
    """Send canvas markdown to Claude and return extracted fields as a dict."""
    client = anthropic.Anthropic(api_key=current_app.config["ANTHROPIC_API_KEY"])

    fields_description = _build_fields_description(config)
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

    extracted = _parse_json_response(message.content[0].text)
    return _enforce_max_lengths(client, config, extracted)


def extract_from_canvas_url(canvas_url: str, config: dict) -> dict:
    """Use Slack MCP to fetch a canvas by URL, then extract fields into a dict."""
    client = anthropic.Anthropic(api_key=current_app.config["ANTHROPIC_API_KEY"])

    fields_description = _build_fields_description(config)
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

    extracted = _parse_message_json(message)
    return _enforce_max_lengths(client, config, extracted)


def _parse_json_response(raw: str) -> dict:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw)
