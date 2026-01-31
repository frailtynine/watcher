from datetime import datetime, timezone


def utcnow_naive():
    """
    Return current UTC time as naive datetime
    (for TIMESTAMP WITHOUT TIME ZONE).
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)
