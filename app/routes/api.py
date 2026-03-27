from flask import Blueprint, current_app, jsonify, request

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
