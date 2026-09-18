from datetime import date
from functools import partial

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget

from project_planner.modules.planning.entities.BacklogItem import BacklogItem
from project_planner.modules.planning.entities.BacklogPriority import BacklogPriority
from project_planner.modules.planning.entities.BacklogStatus import BacklogStatus
from project_planner.modules.planning.entities.Sprint import Sprint
from project_planner.modules.planning.entities.SprintStatus import SprintStatus
from project_planner_frontend.planning.clients.AgileClient import AgileClient
from project_planner_frontend.planning.views.agile.BacklogItemEditorPopup import (
    BacklogItemEditorPopup,
)
from project_planner_frontend.planning.views.agile.SprintDetailsPopup import SprintDetailsPopup
from project_planner_frontend.planning.views.agile.SprintEditorPopup import SprintEditorPopup
from project_planner_frontend.shared.SimpleTabbedPanel import SimpleTabbedPanel
from project_planner_frontend.shared.theme import (
    NAVY_900,
    SLATE_400,
    caption_label,
    paint_background,
    section_label,
    style_button,
    title_label,
)


class AgilePlanningPanel(BoxLayout):
    def __init__(self, agile: AgileClient, **kwargs: object) -> None:
        super().__init__(orientation="vertical", spacing=dp(8), **kwargs)
        self._agile = agile
        self._project_id: str | None = None
        self._section_id: str | None = None
        paint_background(self, NAVY_900)
        self.add_widget(title_label("Agile roadmap"))
        self.add_widget(
            caption_label("Plan the roadmap in the backlog and open sprints from the directory.")
        )
        self._backlog = self._list_area()
        self._sprints = self._list_area()
        self.add_widget(
            SimpleTabbedPanel(
                {
                    "Backlog": self._backlog[0],
                    "Sprint Directory": self._sprints[0],
                }
            )
        )

    def show_context(self, project_id: str, section_id: str | None = None) -> None:
        self._project_id = project_id
        self._section_id = section_id
        self.refresh()

    def refresh(self) -> None:
        for _container, rows in (self._backlog, self._sprints):
            rows.clear_widgets()
        if self._project_id is None:
            return
        items = list(self._agile.list_items(self._project_id, self._section_id))
        self._render_backlog(items)
        self._render_sprints()

    def _render_backlog(self, items: list[BacklogItem]) -> None:
        rows = self._backlog[1]
        add = style_button(Button(text="+ Add backlog item"), "primary")
        add.bind(on_release=self._add_item)
        rows.add_widget(self._action_row(add))
        backlog = [
            item
            for item in items
            if item.sprint_id is None and item.status is not BacklogStatus.DONE
        ]
        if not backlog:
            self._empty(rows, "Backlog is empty.")
        for item in backlog:
            rows.add_widget(self._item_row(item, reorder=True))

    def _render_sprints(self) -> None:
        rows = self._sprints[1]
        if self._project_id is None:
            return
        add = style_button(Button(text="+ Add sprint"), "primary")
        add.bind(on_release=self._add_sprint)
        rows.add_widget(self._action_row(add))
        sprints = list(self._agile.list_sprints(self._project_id, self._section_id))
        if not sprints:
            self._empty(rows, "No sprints in the roadmap yet.")
            return
        planned = [sprint for sprint in sprints if sprint.status is not SprintStatus.COMPLETED]
        completed = [sprint for sprint in sprints if sprint.status is SprintStatus.COMPLETED]
        for heading, group in (("Planned", planned), ("Completed", completed)):
            rows.add_widget(section_label(f"{heading} sprints"))
            if not group:
                self._empty(rows, f"No {heading.lower()} sprints.")
            for sprint in group:
                rows.add_widget(
                    self._sprint_row(
                        sprint,
                        allow_completion=sprint.status is not SprintStatus.COMPLETED,
                    )
                )

    def _sprint_row(self, sprint: Sprint, *, allow_completion: bool) -> BoxLayout:
        row = BoxLayout(
            size_hint_y=None,
            height=dp(72),
            spacing=dp(6),
            padding=[dp(18), 0, 0, 0],
        )
        open_sprint = style_button(
            Button(
                text=(
                    f"{sprint.name}  ·  {sprint.start_date} → {sprint.end_date}\n"
                    f"{sprint.status.value.title()} · Goal: {sprint.goal or 'No goal'}"
                ),
                halign="left",
            ),
            "quiet",
        )
        open_sprint.bind(on_release=partial(self._open_sprint, sprint))
        row.add_widget(open_sprint)
        if allow_completion:
            finish = style_button(
                Button(text="Complete", size_hint_x=None, width=dp(110)),
                "secondary",
            )
            finish.bind(on_release=partial(self._complete_sprint, sprint.id))
            row.add_widget(finish)
        return row

    def _open_sprint(self, sprint: Sprint, *_: object) -> None:
        SprintDetailsPopup(sprint, self._agile, self.refresh).open()

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
        remove = style_button(Button(text="Delete", size_hint_x=None, width=dp(76)), "danger")
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

    @staticmethod
    def _action_row(button: Button) -> BoxLayout:
        row = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
        row.add_widget(Widget())
        button.size_hint_x = None
        button.width = dp(190)
        row.add_widget(button)
        return row
