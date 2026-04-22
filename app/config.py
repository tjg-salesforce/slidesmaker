import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ["FLASK_SECRET_KEY"]
    ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
    GOOGLE_CLIENT_ID = os.environ["GOOGLE_CLIENT_ID"]
    GOOGLE_CLIENT_SECRET = os.environ["GOOGLE_CLIENT_SECRET"]
    GOOGLE_REFRESH_TOKEN = os.environ["GOOGLE_REFRESH_TOKEN"]
    SLIDES_TEMPLATE_ID = os.environ["SLIDES_TEMPLATE_ID"]
    API_KEY = os.environ["API_KEY"]
    SLACK_TOKEN = os.environ.get("SLACK_TOKEN")
    SLACK_MCP_URL = os.environ.get("SLACK_MCP_URL", "https://mcp.slack.com/mcp")
    ADMIN_SLACK_USER_ID = os.environ.get("ADMIN_SLACK_USER_ID")
    SLACK_ENDPOINT_ALLOWED_DOMAINS = [
        d.strip().lower()
        for d in os.environ.get("SLACK_ENDPOINT_ALLOWED_DOMAINS", "salesforce.com").split(",")
        if d.strip()
    ]
    SLACK_ENDPOINT_RATE_LIMIT = int(os.environ.get("SLACK_ENDPOINT_RATE_LIMIT", "5"))
    SLACK_ENDPOINT_RATE_WINDOW_SEC = int(os.environ.get("SLACK_ENDPOINT_RATE_WINDOW_SEC", "900"))
    SQLALCHEMY_DATABASE_URI = os.environ["DATABASE_URL"].replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
