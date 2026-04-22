import json
import logging
import os

from flask import current_app

from app import db
from app.models import Generation
from app.services import claude_service, google_service

logger = logging.getLogger(__name__)


def _load_config(config_name: str = "default") -> dict:
    config_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "extraction_configs",
        f"{config_name}.json",
    )
    with open(os.path.abspath(config_path)) as f:
        return json.load(f)


def generate_deck(
    pdf_bytes: bytes,
    user_email: str,
    title: str,
    pdf_filename: str = None,
    config_name: str = "default",
) -> Generation:
    """Full pipeline: extract from PDF → copy template → fill → share → save."""
    config = _load_config(config_name)

    record = Generation(
        user_email=user_email,
        pdf_filename=pdf_filename,
        status="extracting",
    )
    db.session.add(record)
    db.session.commit()

    try:
        extracted = claude_service.extract_from_pdf(pdf_bytes, config)
        record.extracted_data = extracted
        record.status = "generating"
        db.session.commit()

        deck_url, presentation_id = _build_deck(extracted, user_email, title)

        record.deck_url = deck_url
        record.presentation_id = presentation_id
        record.status = "done"
        db.session.commit()
    except Exception:
        record.status = "error"
        db.session.commit()
        raise

    return record


def extract_canvas_text_into(record_id: int, canvas_text: str, config_name: str = "qbr") -> None:
    """Extract from pasted canvas markdown into an existing Generation record."""
    _extract_into(
        record_id=record_id,
        config_name=config_name,
        extract_fn=lambda cfg: claude_service.extract_from_canvas(canvas_text, cfg),
    )


def extract_canvas_url_into(record_id: int, canvas_url: str, config_name: str = "qbr") -> None:
    """Fetch canvas via Slack MCP and extract into an existing Generation record."""
    _extract_into(
        record_id=record_id,
        config_name=config_name,
        extract_fn=lambda cfg: claude_service.extract_from_canvas_url(canvas_url, cfg),
    )


def _extract_into(record_id: int, config_name: str, extract_fn) -> None:
    config = _load_config(config_name)
    record = Generation.query.get(record_id)
    record.status = "extracting"
    db.session.commit()

    try:
        extracted = extract_fn(config)
        record.extracted_data = extracted
        record.status = "pending_review"
        db.session.commit()
    except Exception:
        record.status = "error"
        db.session.commit()
        raise


def generate_deck_from_data(
    extracted_data: dict,
    user_email: str,
    title: str,
    generation_id: int = None,
) -> Generation:
    """Pipeline starting from already-extracted data (admin review flow)."""
    if generation_id:
        record = Generation.query.get(generation_id)
        record.extracted_data = extracted_data
        record.status = "generating"
    else:
        record = Generation(
            user_email=user_email,
            extracted_data=extracted_data,
            status="generating",
        )
        db.session.add(record)
    db.session.commit()

    try:
        deck_url, presentation_id = _build_deck(extracted_data, user_email, title)
        record.deck_url = deck_url
        record.presentation_id = presentation_id
        record.status = "done"
        db.session.commit()
    except Exception:
        record.status = "error"
        db.session.commit()
        raise

    return record


def _build_deck(extracted_data: dict, user_email: str, title: str):
    presentation_id = google_service.copy_template(title)
    google_service.replace_placeholders(presentation_id, extracted_data)
    google_service.set_permissions(presentation_id, user_email)
    deck_url = google_service.get_deck_url(presentation_id)
    return deck_url, presentation_id


MIN_FILL_RATIO = 0.25  # extracted dict must have >=25% populated fields, else treat as parse failure


def _populated_count(extracted: dict) -> int:
    return sum(1 for v in extracted.values() if isinstance(v, str) and v.strip())


def _fill_ratio(extracted: dict) -> float:
    if not extracted:
        return 0.0
    return _populated_count(extracted) / len(extracted)


def _extract_with_fallback(canvas_url: str, canvas_content: str, config: dict) -> dict:
    """Try content-first, fall back to MCP url path if content yields sparse data."""
    if canvas_content:
        logger.info(
            "Extracting from canvas_content (length=%d, preview=%r)",
            len(canvas_content), canvas_content[:200],
        )
        extracted = claude_service.extract_from_canvas(canvas_content, config)
        ratio = _fill_ratio(extracted)
        logger.info(
            "canvas_content extraction: %d/%d populated (%.0f%%)",
            _populated_count(extracted), len(extracted), ratio * 100,
        )
        if ratio >= MIN_FILL_RATIO:
            return extracted
        logger.warning(
            "canvas_content extraction below fill threshold; content may be truncated or mangled."
        )
        if not canvas_url:
            raise RuntimeError(
                f"Canvas content extraction incomplete "
                f"({_populated_count(extracted)}/{len(extracted)} fields populated) "
                "and no canvas_url fallback provided."
            )
        logger.info("Falling back to canvas_url + MCP path.")

    if not canvas_url:
        raise RuntimeError("Must provide canvas_url or canvas_content.")

    logger.info("Extracting from canvas_url via MCP: %s", canvas_url)
    return claude_service.extract_from_canvas_url(canvas_url, config)


def generate_deck_auto(
    record_id: int,
    canvas_url: str,
    canvas_content: str,
    user_email: str,
    slack_user_id: str,
    title: str,
    config_name: str = "qbr",
) -> None:
    """End-to-end auto flow for Slackbot-triggered runs: extract → build → DM.

    Accepts either canvas_url (MCP path) or canvas_content (raw markdown) or
    both. Content is preferred; URL is used as fallback if content extraction
    yields a sparsely-populated result. Skips the manual review step.
    """
    from app.services import slack_service

    config = _load_config(config_name)
    record = Generation.query.get(record_id)
    admin_user_id = current_app.config.get("ADMIN_SLACK_USER_ID")

    try:
        record.status = "extracting"
        db.session.commit()
        extracted = _extract_with_fallback(canvas_url, canvas_content, config)
        record.extracted_data = extracted

        record.status = "generating"
        db.session.commit()
        deck_url, presentation_id = _build_deck(extracted, user_email, title)
        record.deck_url = deck_url
        record.presentation_id = presentation_id
        record.status = "done"
        db.session.commit()

        slack_service.send_dm(
            slack_user_id,
            f"Your QBR deck is ready: {deck_url}",
        )
    except Exception as exc:
        logger.exception("Auto pipeline failed for record %s", record_id)
        record.status = "error"
        db.session.commit()

        slack_service.send_dm(
            slack_user_id,
            "There was an issue generating your QBR deck. The team has been notified and will look into it.",
        )
        if admin_user_id:
            slack_service.send_dm(
                admin_user_id,
                (
                    f":warning: QBR deck generation failed\n"
                    f"record_id: {record_id}\n"
                    f"user: {user_email} ({slack_user_id})\n"
                    f"inputs: url={bool(canvas_url)}, content_len={len(canvas_content or '')}\n"
                    f"error: {type(exc).__name__}: {exc}"
                ),
            )
        raise
