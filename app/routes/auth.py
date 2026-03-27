from flask import Blueprint, current_app, redirect, request, url_for
from google_auth_oauthlib.flow import Flow

auth_bp = Blueprint("auth", __name__)

SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/presentations",
]


def _build_flow():
    return Flow.from_client_config(
        {
            "web": {
                "client_id": current_app.config["GOOGLE_CLIENT_ID"],
                "client_secret": current_app.config["GOOGLE_CLIENT_SECRET"],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=SCOPES,
        redirect_uri=url_for("auth.oauth_callback", _external=True),
    )


@auth_bp.route("/authorize")
def authorize():
    flow = _build_flow()
    auth_url, _ = flow.authorization_url(access_type="offline", prompt="consent")
    return redirect(auth_url)


@auth_bp.route("/oauth/callback")
def oauth_callback():
    flow = _build_flow()
    flow.fetch_token(authorization_response=request.url)
    refresh_token = flow.credentials.refresh_token
    return (
        f"<h2>OAuth complete</h2>"
        f"<p>Copy this refresh token into your Heroku config as "
        f"<code>GOOGLE_REFRESH_TOKEN</code>:</p>"
        f"<pre>{refresh_token}</pre>"
    )
