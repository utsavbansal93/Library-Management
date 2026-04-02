"""
Reading status cache update logic.

Called within the same transaction as ActivityLedger inserts
to keep the reading_status table in sync.
"""

from datetime import datetime

from typing import Optional

from sqlalchemy.orm import Session

from models import ReadingStatus, EventType, ReadingStatusEnum, _uuid


# Map event types to reading status transitions
_STATUS_MAP = {
    EventType.STARTED_READING.value: ReadingStatusEnum.READING.value,
    EventType.FINISHED_READING.value: ReadingStatusEnum.FINISHED.value,
    EventType.ABANDONED_DNF.value: ReadingStatusEnum.DNF.value,
}


def update_reading_status(
    db: Session,
    user_profile: str,
    work_id: str,
    event_type: str,
    event_value: Optional[str],
    timestamp: datetime,
) -> ReadingStatus:
    """Upsert reading_status cache based on an activity event."""
    row = (
        db.query(ReadingStatus)
        .filter(
            ReadingStatus.user_profile == user_profile,
            ReadingStatus.work_id == work_id,
        )
        .first()
    )

    if row is None:
        row = ReadingStatus(
            id=_uuid(),
            user_profile=user_profile,
            work_id=work_id,
        )
        db.add(row)

    # Update status if this event type maps to a status change
    new_status = _STATUS_MAP.get(event_type)
    if new_status:
        row.status = new_status

    # Update rating if this is a Rated event
    if event_type == EventType.RATED.value and event_value:
        try:
            row.current_rating = float(event_value)
        except ValueError:
            pass

    row.last_event_at = timestamp
    return row
