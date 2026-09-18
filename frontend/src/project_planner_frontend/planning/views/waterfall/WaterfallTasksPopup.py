from collections.abc import Callable
from datetime import date
from functools import partial

from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView

from project_planner.modules.planning.entities.Phase import Phase
from project_planner.modules.planning.entities.WaterfallTask import WaterfallTask
from project_planner.modules.planning.entities.WaterfallTaskStatus import WaterfallTaskStatus
from project_planner_frontend.planning.clients.WaterfallTaskClient import WaterfallTaskClient
from project_planner_frontend.planning.views.waterfall.WaterfallTaskEditorPopup import (
    WaterfallTaskEditorPopup,
)
from project_planner_frontend.shared.date_parser import format_optional_date
from project_planner_frontend.shared.theme import (
    GOLD,
    NAVY_800,
    PEARL_GREY,
    SLATE_400,
    paint_background,
    style_button,
)


class WaterfallTasksPopup(Popup):
    def __init__(
        self,
        tasks: WaterfallTaskClient,
        phase: Phase,
        on_change: Callable[[], None],
        **kwargs: object,
    ) -> None:
        self._tasks = tasks
        self._phase = phase
        self._on_change = on_change
        content = self._build()
        super().__init__(
            title=f"Tasks · {phase.name}",
            title_color=PEARL_GREY,
            separator_color=GOLD,
            background_color=NAVY_800,
            content=content,
            size_hint=(None, None),
            width=min(Window.width * 0.95, dp(900)),
            height=min(Window.height * 0.94, dp(760)),
            **kwargs,
        )
        self.refresh()

    def _build(self) -> BoxLayout:
        content = BoxLayout(orientation="vertical", spacing=dp(8), padding=dp(12))
        paint_background(content, NAVY_800)
        add = style_button(Button(text="+ Add task", size_hint_y=None, height=dp(44)), "primary")
        add.bind(on_release=self._add)
        content.add_widget(add)
        self._rows = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(6))
        self._rows.bind(minimum_height=self._rows.setter("height"))
        scroll = ScrollView(do_scroll_x=False)
        scroll.add_widget(self._rows)
        content.add_widget(scroll)
        close = style_button(Button(text="Close", size_hint_y=None, height=dp(44)), "secondary")
        close.bind(on_release=lambda *_: self.dismiss())
        content.add_widget(close)
        return content

    def refresh(self) -> None:
        self._rows.clear_widgets()
        items = list(self._tasks.list_for_phase(self._phase.id))
        if not items:
            self._rows.add_widget(
                Label(
                    text="No tasks in this phase.", color=SLATE_400, size_hint_y=None, height=dp(54)
                )
            )
        for task in items:
            row = BoxLayout(size_hint_y=None, height=dp(62), spacing=dp(6))
            edit = style_button(
                Button(
                    text=(
                        f"{task.title}\n{task.status.value.replace('_', ' ').title()} · "
                        f"{format_optional_date(task.start_date) or 'No start'} → "
                        f"{format_optional_date(task.due_date) or 'No due date'}"
                    ),
                    halign="left",
                ),
                "quiet",
            )
            edit.bind(on_release=partial(self._edit, task))
            remove = style_button(Button(text="Delete", size_hint_x=None, width=dp(76)), "danger")
            remove.bind(on_release=partial(self._remove, task.id))
            row.add_widget(edit)
            row.add_widget(remove)
            self._rows.add_widget(row)

    def _add(self, *_: object) -> None:
        WaterfallTaskEditorPopup(None, self._create).open()

    def _create(
        self,
        title: str,
        description: str,
        assignee: str,
        start_date: date | None,
        due_date: date | None,
        status: WaterfallTaskStatus,
    ) -> None:
        self._tasks.add(self._phase.id, title, description, assignee, start_date, due_date, status)
        self._changed()

    def _edit(self, task: WaterfallTask, *_: object) -> None:
        def save(
            title: str,
            description: str,
            assignee: str,
            start_date: date | None,
            due_date: date | None,
            status: WaterfallTaskStatus,
        ) -> None:
            self._tasks.update(
                task.id,
                title=title.strip(),
                description=description.strip(),
                assignee=assignee.strip(),
                start_date=start_date,
                due_date=due_date,
                status=status,
            )
            self._changed()

        WaterfallTaskEditorPopup(task, save).open()

    def _remove(self, task_id: str, *_: object) -> None:
        self._tasks.remove(task_id)
        self._changed()

    def _changed(self) -> None:
        self.refresh()
        self._on_change()
