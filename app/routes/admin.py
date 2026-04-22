import json
import logging
import os
import threading

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for

from app import db
from app.models import Generation
from app.services import claude_service, pipeline

logger = logging.getLogger(__name__)

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


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


@admin_bp.route("/", methods=["GET"])
def index():
    return redirect(url_for("admin.canvas"))


@admin_bp.route("/canvas", methods=["GET", "POST"])
def canvas():
    if request.method == "GET":
        return render_template("admin/canvas.html")

    canvas_url = request.form.get("canvas_url", "").strip()
    canvas_text = request.form.get("canvas_text", "").strip()
    user_email = request.form.get("user_email", "").strip()
    title = request.form.get("title", "").strip() or f"QBR Deck for {user_email}"

    if not canvas_url and not canvas_text:
        flash("Provide a canvas URL or paste canvas content.", "error")
        return redirect(url_for("admin.canvas"))
    if not user_email:
        flash("Recipient email is required.", "error")
        return redirect(url_for("admin.canvas"))

    record = Generation(user_email=user_email, status="queued")
    db.session.add(record)
    db.session.commit()
    record_id = record.id

    app = current_app._get_current_object()

    def _run_extraction():
        with app.app_context():
            try:
                if canvas_url:
                    pipeline.extract_canvas_url_into(record_id, canvas_url)
                else:
                    pipeline.extract_canvas_text_into(record_id, canvas_text)
            except Exception:
                app.logger.exception("Background extraction failed for record %s", record_id)

    threading.Thread(target=_run_extraction, daemon=True).start()

    return redirect(url_for("admin.status", id=record_id, title=title))


@admin_bp.route("/status/<int:id>")
def status(id):
    record = Generation.query.get_or_404(id)
    title = request.args.get("title") or f"Deck #{id}"

    if record.status == "pending_review":
        return redirect(url_for("admin.review", id=id, title=title))

    return render_template(
        "admin/status.html",
        record=record,
        title=title,
        is_error=(record.status == "error"),
    )


@admin_bp.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "GET":
        return render_template("admin/upload.html")

    if "pdf" not in request.files or request.files["pdf"].filename == "":
        flash("Please select a PDF file.", "error")
        return redirect(url_for("admin.upload"))

    pdf_file = request.files["pdf"]
    user_email = request.form.get("user_email", "").strip()
    title = request.form.get("title", "").strip() or f"Deck for {user_email}"

    if not user_email:
        flash("Recipient email is required.", "error")
        return redirect(url_for("admin.upload"))

    config = _load_config()

    try:
        extracted = claude_service.extract_from_pdf(pdf_file.read(), config)
    except Exception as e:
        flash(f"Extraction failed: {e}", "error")
        return redirect(url_for("admin.upload"))

    record = Generation(
        user_email=user_email,
        pdf_filename=pdf_file.filename,
        extracted_data=extracted,
        status="pending_review",
    )
    db.session.add(record)
    db.session.commit()

    return redirect(url_for("admin.review", id=record.id, title=title))


@admin_bp.route("/review/<int:id>", methods=["GET", "POST"])
def review(id):
    record = Generation.query.get_or_404(id)
    title = request.args.get("title") or request.form.get("title") or f"Deck #{id}"

    if request.method == "POST":
        updated_data = {
            key: request.form[key]
            for key in record.extracted_data
            if key in request.form
        }
        try:
            updated_record = pipeline.generate_deck_from_data(
                extracted_data=updated_data,
                user_email=record.user_email,
                title=title,
                generation_id=id,
            )
        except Exception as e:
            logger.exception("Generation failed")
            flash(f"Generation failed: {e}", "error")
            return redirect(url_for("admin.review", id=id, title=title))

        return redirect(url_for("admin.history"))

    return render_template(
        "admin/review.html",
        fields=record.extracted_data,
        user_email=record.user_email,
        title=title,
        id=id,
    )


@admin_bp.route("/history")
def history():
    generations = Generation.query.order_by(Generation.created_at.desc()).all()
    return render_template("admin/history.html", generations=generations)
