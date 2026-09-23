from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from typing import TypeVar

from kivy.clock import Clock

from project_planner_frontend.shared.dialogs import show_error

T = TypeVar("T")
_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="planner-io")


def run_background(
    operation: Callable[[], T],
    on_success: Callable[[T], None],
    on_error: Callable[[Exception], None] | None = None,
) -> None:
    future = _executor.submit(operation)

    def completed(_future: object) -> None:
        def deliver(_elapsed: float) -> None:
            try:
                result = future.result()
            except Exception as error:
                if on_error is None:
                    show_error(str(error))
                else:
                    on_error(error)
            else:
                on_success(result)

        Clock.schedule_once(deliver, 0)

    future.add_done_callback(completed)
