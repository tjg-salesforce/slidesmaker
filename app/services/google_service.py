from flask import current_app
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/presentations",
]


def get_credentials():
    return Credentials(
        token=None,
        refresh_token=current_app.config["GOOGLE_REFRESH_TOKEN"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=current_app.config["GOOGLE_CLIENT_ID"],
        client_secret=current_app.config["GOOGLE_CLIENT_SECRET"],
        scopes=SCOPES,
    )


def copy_template(title: str) -> str:
    """Copy the Slides template and return the new presentation ID."""
    creds = get_credentials()
    drive = build("drive", "v3", credentials=creds)
    result = (
        drive.files()
        .copy(
            fileId=current_app.config["SLIDES_TEMPLATE_ID"],
            body={"name": title},
        )
        .execute()
    )
    return result["id"]


def replace_placeholders(presentation_id: str, replacements: dict) -> None:
    """Replace {{key}} tokens in the presentation with values from replacements."""
    creds = get_credentials()
    slides = build("slides", "v1", credentials=creds)
    requests = [
        {
            "replaceAllText": {
                "containsText": {"text": f"{{{{{key}}}}}", "matchCase": True},
                "replaceText": str(value),
            }
        }
        for key, value in replacements.items()
    ]
    slides.presentations().batchUpdate(
        presentationId=presentation_id,
        body={"requests": requests},
    ).execute()


def set_permissions(presentation_id: str, user_email: str) -> None:
    """Grant editor access to user_email and viewer access to @salesforce.com domain."""
    creds = get_credentials()
    drive = build("drive", "v3", credentials=creds)

    drive.permissions().create(
        fileId=presentation_id,
        body={"type": "user", "role": "writer", "emailAddress": user_email},
        sendNotificationEmail=False,
    ).execute()

    drive.permissions().create(
        fileId=presentation_id,
        body={"type": "domain", "role": "reader", "domain": "salesforce.com"},
    ).execute()


def get_deck_url(presentation_id: str) -> str:
    return f"https://docs.google.com/presentation/d/{presentation_id}/edit"
