import base64
import json

import anthropic
from flask import current_app


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

    raw = message.content[0].text.strip()
    # Strip markdown fences if Claude wraps the JSON
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw)
