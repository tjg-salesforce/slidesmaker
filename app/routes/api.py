import json
import threading
import time
from collections import defaultdict, deque
from threading import Lock

import requests as http_requests
from flask import Blueprint, Response, current_app, jsonify, request, stream_with_context

from app import db
from app.models import Generation
from app.services import pipeline

KEEPALIVE_INTERVAL_SEC = 15

api_bp = Blueprint("api", __name__, url_prefix="/api")

_rate_limit_log: dict = defaultdict(deque)
_rate_limit_lock = Lock()


def _check_auth():
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return False
    return auth[len("Bearer "):] == current_app.config["API_KEY"]


def _email_domain_allowed(email: str) -> bool:
    allowed = current_app.config.get("SLACK_ENDPOINT_ALLOWED_DOMAINS") or []
    if not allowed:
        return True
    parts = email.rsplit("@", 1)
    if len(parts) != 2:
        return False
    return parts[1].lower() in allowed


def _rate_limit_check(slack_user_id: str) -> tuple[bool, int]:
    """Sliding-window rate limit. Returns (allowed, retry_after_seconds)."""
    limit = current_app.config["SLACK_ENDPOINT_RATE_LIMIT"]
    window = current_app.config["SLACK_ENDPOINT_RATE_WINDOW_SEC"]
    now = time.time()
    cutoff = now - window

    with _rate_limit_lock:
        timestamps = _rate_limit_log[slack_user_id]
        while timestamps and timestamps[0] < cutoff:
            timestamps.popleft()
        if len(timestamps) >= limit:
            retry_after = int(timestamps[0] + window - now) + 1
            return False, retry_after
        timestamps.append(now)
        return True, 0


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
    """Slackbot-triggered synchronous deck generation.

    Body (JSON): {email, slack_user_id, canvas_url?, canvas_content?}
      - Must provide at least one of canvas_url or canvas_content.
      - If both provided, canvas_content is tried first; canvas_url is used
        as fallback when content extraction yields sparse data.
      - slack_user_id is kept for per-user rate limiting + logging.
    No Bearer auth: scope-fenced by email-domain allowlist + per-user rate
    limit so the skill canvas can be widely shared without a secret.
    Response: 200 OK with streamed keep-alive whitespace during the ~60–90s
    pipeline, followed by JSON.
      - success: {"deck_url": "..."}
      - failure mid-pipeline: {"error": "generation_failed", "message": "..."}
    Pre-stream validation still returns proper 400/403/429.
    """
    data = request.get_json(silent=True) or {}
    canvas_url = (data.get("canvas_url") or "").strip()
    canvas_content = data.get("canvas_content") or ""
    email = (data.get("email") or "").strip()
    slack_user_id = (data.get("slack_user_id") or "").strip()

    if not canvas_url and not canvas_content:
        return jsonify({"error": "Missing canvas_url or canvas_content (at least one required)"}), 400

    missing = [
        k for k, v in {"email": email, "slack_user_id": slack_user_id}.items() if not v
    ]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    if not _email_domain_allowed(email):
        allowed = current_app.config.get("SLACK_ENDPOINT_ALLOWED_DOMAINS") or []
        current_app.logger.warning(
            "slack/generate rejected: disallowed email domain email=%s user=%s",
            email, slack_user_id,
        )
        return jsonify({
            "error": f"email domain not allowed (allowed: {', '.join(allowed)})"
        }), 403

    allowed, retry_after = _rate_limit_check(slack_user_id)
    if not allowed:
        current_app.logger.warning(
            "slack/generate rate-limited: user=%s retry_after=%ds", slack_user_id, retry_after,
        )
        response = jsonify({
            "error": "rate limit exceeded",
            "retry_after_seconds": retry_after,
        })
        response.status_code = 429
        response.headers["Retry-After"] = str(retry_after)
        return response

    record = Generation(user_email=email, status="queued")
    db.session.add(record)
    db.session.commit()
    record_id = record.id
    title = f"QBR Deck for {email}"

    current_app.logger.info(
        "slack/generate accepted: record=%d user=%s email=%s url=%s content_len=%d ip=%s",
        record_id, slack_user_id, email, bool(canvas_url), len(canvas_content),
        request.headers.get("X-Forwarded-For", request.remote_addr),
    )

    flask_app = current_app._get_current_object()
    work_result: dict = {}

    def _work():
        with flask_app.app_context():
            try:
                deck_url = pipeline.generate_deck_sync(
                    record_id=record_id,
                    canvas_url=canvas_url,
                    canvas_content=canvas_content,
                    user_email=email,
                    title=title,
                )
                work_result["deck_url"] = deck_url
            except Exception as exc:
                work_result["error"] = f"{type(exc).__name__}: {exc}"

    def _stream():
        t = threading.Thread(target=_work, daemon=True)
        t.start()
        # Flush response headers immediately so Heroku's 30s first-byte
        # timer is satisfied even though the pipeline runs 60–90s.
        yield " "
        while True:
            t.join(timeout=KEEPALIVE_INTERVAL_SEC)
            if not t.is_alive():
                break
            yield " "
        if "deck_url" in work_result:
            flask_app.logger.info(
                "slack/generate completed: record=%d deck_url=%s",
                record_id, work_result["deck_url"],
            )
            yield json.dumps({"deck_url": work_result["deck_url"]})
        else:
            flask_app.logger.warning(
                "slack/generate failed: record=%d error=%s",
                record_id, work_result.get("error"),
            )
            yield json.dumps({
                "error": "generation_failed",
                "message": work_result.get("error", "unknown error"),
            })

    return Response(
        stream_with_context(_stream()),
        mimetype="application/json",
    )


@api_bp.route("/appscript/generate", methods=["POST"])
def appscript_generate():
    """Proxy: forward token payload to Apps Script and return the deck URL."""
    apps_script_url = current_app.config.get("APPS_SCRIPT_URL")
    if not apps_script_url:
        return jsonify({"error": "APPS_SCRIPT_URL not configured"}), 500

    data = request.get_json(silent=True) or {}

    if not data.get("user_email"):
        return jsonify({"error": "missing user_email"}), 400
    if not data.get("replacements"):
        return jsonify({"error": "missing replacements"}), 400

    resp = http_requests.post(apps_script_url, json=data, timeout=120)
    try:
        result = resp.json()
    except Exception:
        return jsonify({"error": "Apps Script returned non-JSON", "body": resp.text[:500]}), 502

    if "error" in result:
        return jsonify(result), 502

    return jsonify(result)
