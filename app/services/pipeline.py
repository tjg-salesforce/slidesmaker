import json
import os

from app import db
from app.models import Generation
from app.services import claude_service, google_service


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
