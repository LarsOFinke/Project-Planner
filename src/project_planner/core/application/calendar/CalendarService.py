import calendar
from datetime import date

from project_planner.core.domain.calendar.CalendarDay import CalendarDay


class CalendarService:
    def month(self, year: int, month: int) -> tuple[tuple[CalendarDay, ...], ...]:
        weeks = calendar.Calendar(firstweekday=calendar.MONDAY).monthdatescalendar(year, month)
        return tuple(
            tuple(CalendarDay(value, value.month == month) for value in week) for week in weeks
        )

    @staticmethod
    def shift_month(value: date, offset: int) -> date:
        month_index = value.year * 12 + value.month - 1 + offset
        year, zero_based_month = divmod(month_index, 12)
        month = zero_based_month + 1
        last_day = calendar.monthrange(year, month)[1]
        return value.replace(year=year, month=month, day=min(value.day, last_day))

    @staticmethod
    def today() -> date:
        return date.today()

    @staticmethod
    def parse_optional(value: str, label: str = "Date") -> date | None:
        normalized = value.strip()
        if not normalized:
            return None
        try:
            return date.fromisoformat(normalized)
        except ValueError as error:
            raise ValueError(f"{label} must use YYYY-MM-DD") from error

    @staticmethod
    def format_optional(value: date | None) -> str:
        return value.isoformat() if value is not None else ""
