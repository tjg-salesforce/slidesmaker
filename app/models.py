from datetime import datetime, timezone

from app import db


class Generation(db.Model):
    __tablename__ = "generations"

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    user_email = db.Column(db.String(255), nullable=False)
    pdf_filename = db.Column(db.String(255))
    extracted_data = db.Column(db.JSON)
    deck_url = db.Column(db.String(512))
    presentation_id = db.Column(db.String(255))
    status = db.Column(db.String(50), default="pending", nullable=False)
