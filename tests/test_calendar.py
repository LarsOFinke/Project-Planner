from datetime import date

import pytest

from project_planner.modules.calendar.services.CalendarService import CalendarService


def test_calendar_builds_monday_first_month_grid_with_adjacent_days() -> None:
    service = CalendarService()

    weeks = service.month(2026, 9)

    assert all(len(week) == 7 for week in weeks)
    assert weeks[0][0].value == date(2026, 8, 31)
    assert weeks[0][0].in_month is False
    assert weeks[0][1].value == date(2026, 9, 1)
    assert weeks[0][1].in_month is True


def test_calendar_month_navigation_clamps_day_and_crosses_years() -> None:
    service = CalendarService()

    assert service.shift_month(date(2024, 1, 31), 1) == date(2024, 2, 29)
    assert service.shift_month(date(2026, 1, 15), -1) == date(2025, 12, 15)


def test_calendar_owns_shared_iso_date_parsing_and_formatting() -> None:
    service = CalendarService()

    assert service.parse_optional(" 2026-09-17 ") == date(2026, 9, 17)
    assert service.parse_optional("") is None
    assert service.format_optional(date(2026, 9, 17)) == "2026-09-17"
    assert service.format_optional(None) == ""
    with pytest.raises(ValueError, match="Due date must use YYYY-MM-DD"):
        service.parse_optional("17.09.2026", "Due date")
