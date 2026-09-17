from datetime import date
from functools import partial

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView

from project_planner.core.application.agile.AgilePlanningService import AgilePlanningService
from project_planner.core.domain.agile.BacklogItem import BacklogItem
from project_planner.core.domain.agile.BacklogPriority import BacklogPriority
from project_planner.core.domain.agile.BacklogStatus import BacklogStatus
from project_planner.frontend.planning.agile.BacklogItemEditorPopup import (
    BacklogItemEditorPopup,
)
from project_planner.frontend.planning.agile.SprintEditorPopup import SprintEditorPopup
from project_planner.frontend.shared.SimpleTabbedPanel import SimpleTabbedPanel
from project_planner.frontend.shared.theme import (
    NAVY_900,
    SLATE_200,
    SLATE_400,
    caption_label,
    paint_background,
    style_button,
    title_label,
)


class AgilePlanningPanel(BoxLayout):
    def __init__(self, agile: AgilePlanningService, **kwargs: object) -> None:
        super().__init__(orientation="vertical", spacing=dp(8), **kwargs)
        self._agile = agile
        self._project_id: str | None = None
        self._section_id: str | None = None
        paint_background(self, NAVY_900)
        self.add_widget(title_label("Agile plan"))
        self.add_widget(caption_label("Backlog → Sprints → Completed"))
        self._backlog = self._list_area()
        self._sprints = self._list_area()
        self._completed = self._list_area()
        self.add_widget(
            SimpleTabbedPanel(
                {
                    "Backlog": self._backlog[0],
                    "Sprints": self._sprints[0],
                    "Completed": self._completed[0],
                }
            )
        )

    def show_context(self, project_id: str, section_id: str | None = None) -> None:
        self._project_id = project_id
        self._section_id = section_id
        self.refresh()

    def refresh(self) -> None:
        for _container, rows in (self._backlog, self._sprints, self._completed):
            rows.clear_widgets()
        if self._project_id is None:
            return
        items = list(self._agile.list_items(self._project_id, self._section_id))
        self._render_backlog(items)
        self._render_sprints(items)
        self._render_completed(items)

    def _render_backlog(self, items: list[BacklogItem]) -> None:
        rows = self._backlog[1]
        add = style_button(
            Button(text="+ Add backlog item", size_hint_y=None, height=dp(44)), "primary"
        )
        add.bind(on_release=self._add_item)
        rows.add_widget(add)
        backlog = [
            item
            for item in items
            if item.sprint_id is None and item.status is not BacklogStatus.DONE
        ]
        if not backlog:
            self._empty(rows, "Backlog is empty.")
        for item in backlog:
            rows.add_widget(self._item_row(item, reorder=True))

    def _render_sprints(self, items: list[BacklogItem]) -> None:
        rows = self._sprints[1]
        if self._project_id is None:
            return
        add = style_button(Button(text="+ Add sprint", size_hint_y=None, height=dp(44)), "primary")
        add.bind(on_release=self._add_sprint)
        rows.add_widget(add)
        sprints = list(self._agile.planned_sprints(self._project_id, self._section_id))
        if not sprints:
            self._empty(rows, "No planned sprints yet.")
        for sprint in sprints:
            rows.add_widget(
                Label(
                    text=(
                        f"{sprint.name}  ·  {sprint.start_date} → {sprint.end_date}\n"
                        f"Goal: {sprint.goal or 'No goal'}"
                    ),
                    color=SLATE_200,
                    halign="left",
                    size_hint_y=None,
                    height=dp(58),
                )
            )
            sprint_items = [item for item in items if item.sprint_id == sprint.id]
            groups = (
                ("To Do", BacklogStatus.BACKLOG),
                ("In Progress", BacklogStatus.IN_PROGRESS),
                ("Done", BacklogStatus.DONE),
            )
            for label, status in groups:
                grouped = [item for item in sprint_items if item.status is status]
                rows.add_widget(
                    Label(
                        text=label,
                        color=SLATE_400,
                        bold=True,
                        halign="left",
                        size_hint_y=None,
                        height=dp(32),
                    )
                )
                for item in grouped:
                    rows.add_widget(self._item_row(item))
                if not grouped:
                    self._empty(rows, "No items")
            finish = style_button(
                Button(text="Complete sprint", size_hint_y=None, height=dp(44)),
                "secondary",
            )
            finish.bind(on_release=partial(self._complete_sprint, sprint.id))
            rows.add_widget(finish)

    def _render_completed(self, items: list[BacklogItem]) -> None:
        rows = self._completed[1]
        completed = [item for item in items if item.status is BacklogStatus.DONE]
        for item in completed:
            rows.add_widget(self._item_row(item))
        if self._project_id is not None:
            for sprint in self._agile.sprint_history(self._project_id, self._section_id):
                rows.add_widget(
                    Label(
                        text=(
                            f"Sprint history · {sprint.name} · "
                            f"{sprint.start_date} → {sprint.end_date}"
                        ),
                        color=SLATE_400,
                        size_hint_y=None,
                        height=dp(36),
                    )
                )
        if not completed:
            self._empty(rows, "No completed items yet.")

    def _item_row(self, item: BacklogItem, reorder: bool = False) -> BoxLayout:
        row = BoxLayout(size_hint_y=None, height=dp(62), spacing=dp(5))
        edit = style_button(
            Button(
                text=(
                    f"{item.title}\n{item.priority.value.title()} · "
                    f"{item.status.value.replace('_', ' ').title()} · "
                    f"{item.assignee or 'Unassigned'}"
                ),
                halign="left",
            ),
            "quiet",
        )
        edit.bind(on_release=partial(self._edit_item, item))
        row.add_widget(edit)
        if reorder:
            for label, offset in (("Up", -1), ("Down", 1)):
                button = style_button(
                    Button(text=label, size_hint_x=None, width=dp(60)), "secondary"
                )
                button.bind(on_release=partial(self._move_item, item.id, offset))
                row.add_widget(button)
        remove = style_button(Button(text="Del", size_hint_x=None, width=dp(54)), "danger")
        remove.bind(on_release=partial(self._remove_item, item.id))
        row.add_widget(remove)
        return row

    def _add_item(self, *_: object) -> None:
        BacklogItemEditorPopup(None, self._create_item).open()

    def _create_item(
        self,
        title: str,
        description: str,
        priority: BacklogPriority,
        _status: BacklogStatus,
        assignee: str,
    ) -> None:
        if self._project_id is not None:
            self._agile.add_item(
                self._project_id,
                title,
                description,
                priority,
                assignee,
                self._section_id,
            )
            self.refresh()

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

        BacklogItemEditorPopup(item, save).open()

    def _move_item(self, item_id: str, offset: int, *_: object) -> None:
        if self._project_id is not None:
            self._agile.move_item(self._project_id, item_id, offset, self._section_id)
            self.refresh()

    def _remove_item(self, item_id: str, *_: object) -> None:
        self._agile.remove_item(item_id)
        self.refresh()

    def _add_sprint(self, *_: object) -> None:
        if self._project_id is None:
            return
        candidates = [
            item
            for item in self._agile.list_items(self._project_id, self._section_id)
            if item.sprint_id is None and item.status is not BacklogStatus.DONE
        ]

        def save(
            name: str,
            start: date,
            end: date,
            goal: str,
            selected: list[str],
        ) -> None:
            if self._project_id is not None:
                self._agile.add_sprint(
                    self._project_id,
                    name,
                    start,
                    end,
                    goal,
                    selected,
                    self._section_id,
                )
                self.refresh()

        SprintEditorPopup(candidates, save).open()

    def _complete_sprint(self, sprint_id: str, *_: object) -> None:
        if self._project_id is not None:
            self._agile.complete_sprint(self._project_id, sprint_id, self._section_id)
            self.refresh()

    @staticmethod
    def _list_area() -> tuple[ScrollView, BoxLayout]:
        rows = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(6), padding=dp(8))
        rows.bind(minimum_height=rows.setter("height"))
        scroll = ScrollView(do_scroll_x=False)
        scroll.add_widget(rows)
        return scroll, rows

    @staticmethod
    def _empty(rows: BoxLayout, text: str) -> None:
        rows.add_widget(Label(text=text, color=SLATE_400, size_hint_y=None, height=dp(54)))
