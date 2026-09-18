from collections.abc import Callable
from functools import partial

from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView

from project_planner.modules.planning.entities.BacklogItem import BacklogItem
from project_planner.modules.planning.entities.BacklogPriority import BacklogPriority
from project_planner.modules.planning.entities.BacklogStatus import BacklogStatus
from project_planner.modules.planning.entities.Sprint import Sprint
from project_planner.modules.planning.entities.SprintStatus import SprintStatus
from project_planner_frontend.planning.clients.AgileClient import AgileClient
from project_planner_frontend.planning.views.agile.BacklogItemEditorPopup import (
    BacklogItemEditorPopup,
)
from project_planner_frontend.shared.SimpleTabbedPanel import SimpleTabbedPanel
from project_planner_frontend.shared.theme import (
    GOLD,
    NAVY_800,
    NAVY_900,
    PEARL_GREY,
    SLATE_400,
    caption_label,
    paint_background,
    style_button,
)


class SprintDetailsPopup(Popup):
    def __init__(
        self,
        sprint: Sprint,
        agile: AgileClient,
        on_change: Callable[[], None],
        **kwargs: object,
    ) -> None:
        self._sprint = sprint
        self._agile = agile
        self._on_change = on_change
        content = self._build()
        super().__init__(
            title=sprint.name,
            title_color=PEARL_GREY,
            separator_color=GOLD,
            background_color=NAVY_800,
            content=content,
            size_hint=(None, None),
            width=Window.width * 0.94,
            height=Window.height * 0.9,
            **kwargs,
        )
        self.refresh()

    def _build(self) -> BoxLayout:
        content = BoxLayout(
            orientation="vertical",
            spacing=dp(8),
            padding=dp(12),
        )
        paint_background(content, NAVY_900)
        content.add_widget(
            caption_label(
                f"{self._sprint.start_date} → {self._sprint.end_date}  ·  "
                f"Goal: {self._sprint.goal or 'No goal'}"
            )
        )
        self._groups = {
            BacklogStatus.BACKLOG: self._list_area(),
            BacklogStatus.IN_PROGRESS: self._list_area(),
            BacklogStatus.DONE: self._list_area(),
        }
        content.add_widget(
            SimpleTabbedPanel(
                {
                    "To Do": self._groups[BacklogStatus.BACKLOG][0],
                    "In Progress": self._groups[BacklogStatus.IN_PROGRESS][0],
                    "Done": self._groups[BacklogStatus.DONE][0],
                }
            )
        )
        close = style_button(Button(text="Close", size_hint_y=None, height=dp(46)), "secondary")
        close.bind(on_release=lambda *_: self.dismiss())
        content.add_widget(close)
        return content

    def refresh(self) -> None:
        for _scroll, rows in self._groups.values():
            rows.clear_widgets()
        items = self._agile.list_sprint_items(
            self._sprint.project_id,
            self._sprint.id,
            self._sprint.section_id,
        )
        for status, (_scroll, rows) in self._groups.items():
            grouped = [item for item in items if item.status is status]
            if not grouped:
                rows.add_widget(
                    Label(
                        text="No items in this state.",
                        color=SLATE_400,
                        size_hint_y=None,
                        height=dp(58),
                    )
                )
                continue
            for item in grouped:
                rows.add_widget(self._item_row(item))

    def _item_row(self, item: BacklogItem) -> BoxLayout:
        row = BoxLayout(size_hint_y=None, height=dp(64), spacing=dp(6))
        assignment = item.assignee or "Unassigned"
        details = style_button(
            Button(
                text=f"{item.title}\n{item.priority.value.title()} · {assignment}",
                halign="left",
            ),
            "quiet",
        )
        details.bind(
            size=lambda widget, size: setattr(widget, "text_size", (size[0] - dp(18), size[1]))
        )
        row.add_widget(details)
        if self._sprint.status is not SprintStatus.COMPLETED:
            details.bind(on_release=partial(self._edit_item, item))
            remove = style_button(Button(text="Remove", size_hint_x=None, width=dp(96)), "danger")
            remove.bind(on_release=partial(self._remove_item, item.id))
            row.add_widget(remove)
        else:
            details.disabled = True
        return row

    def _edit_item(self, item: BacklogItem, *_: object) -> None:
        def save(
            title: str,
            description: str,
            priority: BacklogPriority,
            status: BacklogStatus,
            assignee: str,
        ) -> None:
            self._agile.update_item(
                item,
                title=title,
                description=description,
                priority=priority,
                status=status,
                assignee=assignee,
            )
            self.refresh()
            self._on_change()

        BacklogItemEditorPopup(item, save).open()

    def _remove_item(self, item_id: str, *_: object) -> None:
        self._agile.remove_item(item_id)
        self.refresh()
        self._on_change()

    @staticmethod
    def _list_area() -> tuple[ScrollView, BoxLayout]:
        rows = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=dp(6),
            padding=dp(8),
        )
        rows.bind(minimum_height=rows.setter("height"))
        scroll = ScrollView(do_scroll_x=False, bar_width=dp(5))
        scroll.add_widget(rows)
        return scroll, rows
