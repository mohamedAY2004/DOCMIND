from datetime import date, datetime, timezone

from services.retention_service import document_expiry, tutor_expiry


def test_tutor_retention_is_term_end_plus_30_days():
    created = datetime(2026, 1, 1, tzinfo=timezone.utc)
    expiry = tutor_expiry(date(2026, 5, 31), created)
    assert expiry.date() == date(2026, 6, 30)


def test_private_chat_without_active_term_uses_180_days():
    created = datetime(2026, 1, 1, tzinfo=timezone.utc)
    assert (document_expiry(None, created) - created).days == 180
