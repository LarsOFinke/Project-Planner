from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class CalendarDay:
    value: date
    in_month: bool
