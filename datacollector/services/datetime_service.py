from datetime import datetime, timezone


class DateTimeService:
    dt: datetime

    def __init__(self, dt: datetime | None):
        self.dt = dt

    def get_datetime(self) -> datetime:
        if self.dt is None:
            # timezone-aware
            return datetime.now(timezone.utc)
        return self.dt
