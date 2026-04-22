import threading

from flask import Blueprint, current_app, jsonify, request

from app import db
from app.models import Generation
from app.services import pipeline

api_bp = Blueprint("api", __name__, url_prefix="/api")


def _check_auth():
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return False
    return auth[len("Bearer "):] == current_app.config["API_KEY"]


@api_bp.route("/generate", methods=["POST"])
def generate():
    if not _check_auth():
        return jsonify({"error": "Unauthorized"}), 401

    if "pdf" not in request.files:
        return jsonify({"error": "Missing pdf file"}), 400

    user_email = request.form.get("user_email")
    if not user_email:
        return jsonify({"error": "Missing user_email"}), 400

    pdf_file = request.files["pdf"]
    title = request.form.get("title") or f"Deck for {user_email}"

    try:
        record = pipeline.generate_deck(
            pdf_bytes=pdf_file.read(),
            user_email=user_email,
            title=title,
            pdf_filename=pdf_file.filename,
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({"deck_url": record.deck_url, "id": record.id})


@api_bp.route("/slack/generate", methods=["POST"])
def slack_generate():
    """Slackbot-triggered auto deck generation.

    Body (JSON): {email, slack_user_id, canvas_url?, canvas_content?}
      - Must provide at least one of canvas_url or canvas_content.
      - If both provided, canvas_content is tried first; canvas_url is used
        as fallback when content extraction yields sparse data.
    Auth: Authorization: Bearer <API_KEY>
    Returns: 202 {generation_id, status} immediately; deck link is DM'd to
    slack_user_id when ready (or an error DM on failure).
    """
    if not _check_auth():
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    canvas_url = (data.get("canvas_url") or "").strip()
    canvas_content = data.get("canvas_content") or ""
    email = (data.get("email") or "").strip()
    slack_user_id = (data.get("slack_user_id") or "").strip()

    if not canvas_url and not canvas_content:
        return jsonify({"error": "Missing canvas_url or canvas_content (at least one required)"}), 400

    missing = [
        k for k, v in {
            "email": email,
            "slack_user_id": slack_user_id,
        }.items() if not v
    ]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    record = Generation(user_email=email, status="queued")
    db.session.add(record)
    db.session.commit()
    record_id = record.id
    title = f"QBR Deck for {email}"

    current_app.logger.info(
        "Slack generate received: record=%d, url=%s, content_len=%d",
        record_id, bool(canvas_url), len(canvas_content),
    )

    flask_app = current_app._get_current_object()

    def _run():
        with flask_app.app_context():
            try:
                pipeline.generate_deck_auto(
                    record_id=record_id,
                    canvas_url=canvas_url,
                    canvas_content=canvas_content,
                    user_email=email,
                    slack_user_id=slack_user_id,
                    title=title,
                )
            except Exception:
                flask_app.logger.exception(
                    "Slack auto-pipeline failed for record %s", record_id
                )

    threading.Thread(target=_run, daemon=True).start()

    return jsonify({"generation_id": record_id, "status": "queued"}), 202
