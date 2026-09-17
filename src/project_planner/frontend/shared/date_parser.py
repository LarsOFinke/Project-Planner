from datetime import date

from project_planner.core.application.calendar.CalendarService import CalendarService

_CALENDAR = CalendarService()


def parse_optional_date(value: str, label: str = "Date") -> date | None:
    return _CALENDAR.parse_optional(value, label)


def format_optional_date(value: date | None) -> str:
    return _CALENDAR.format_optional(value)
