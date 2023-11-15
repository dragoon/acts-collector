from datetime import datetime, timezone


def string_to_date(date_string: str):
    return datetime.strptime(date_string, '%Y-%m-%d').replace(tzinfo=timezone.utc)
