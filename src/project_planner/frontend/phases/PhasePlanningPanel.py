from functools import partial

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView

from project_planner.core.application.phases.PhaseService import PhaseService
from project_planner.core.application.projects.ProjectWorkflowService import (
    ProjectWorkflowService,
)
from project_planner.core.application.todos.TodoService import TodoService
from project_planner.core.domain.phases.Phase import Phase
from project_planner.core.domain.phases.PhaseStatus import PhaseStatus
from project_planner.core.domain.todos.TodoModule import TodoModule
from project_planner.frontend.phases.PhaseEditorPopup import PhaseEditorPopup
from project_planner.frontend.shared.theme import (
    NAVY_900,
    RED,
    SLATE_400,
    caption_label,
    paint_background,
    style_button,
    title_label,
)
from project_planner.frontend.todos.TodoManagerPopup import TodoManagerPopup


class PhasePlanningPanel(BoxLayout):
    def __init__(
        self,
        phases: PhaseService,
        workflows: ProjectWorkflowService,
        todos: TodoService,
        **kwargs: object,
    ) -> None:
        super().__init__(
            orientation="vertical",
            spacing=dp(10),
            padding=[dp(22), dp(18)],
            **kwargs,
        )
        self._phases = phases
        self._workflows = workflows
        self._todos = todos
        self._project_id: str | None = None
        paint_background(self, NAVY_900)
        self.add_widget(title_label("Phase planning"))
        self.add_widget(
            caption_label("Shape the delivery flow, then reorder phases as work evolves.")
        )
        controls = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
        add = style_button(Button(text="+ Add phase"), "primary")
        reset = style_button(Button(text="Reset from template"), "danger")
        add.bind(on_release=self._add)
        reset.bind(on_release=self._reset)
        controls.add_widget(add)
        controls.add_widget(reset)
        self._rows = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(5))
        self._rows.bind(minimum_height=self._rows.setter("height"))
        scroll = ScrollView(do_scroll_x=False, bar_width=dp(5))
        scroll.add_widget(self._rows)
        self.add_widget(controls)
        self.add_widget(scroll)
        self.disabled = True

    def show_project(self, project_id: str) -> None:
        self._project_id = project_id
        self.disabled = False
        self.refresh()

    def refresh(self) -> None:
        self._rows.clear_widgets()
        if self._project_id is None:
            return
        phases = self._phases.list_for_project(self._project_id)
        if not phases:
            self._rows.add_widget(
                Label(
                    text="No phases yet. Add one or load the selected planning template.",
                    color=SLATE_400,
                    size_hint_y=None,
                    height=dp(70),
                )
            )
            return
        for phase in phases:
            row = BoxLayout(size_hint_y=None, height=dp(64), spacing=dp(6))
            summary = phase.description.strip() or "No description"
            edit = style_button(
                Button(
                    text=(
                        f"{phase.position + 1:02}.  {phase.name}\n"
                        f"{phase.status.value.title()}  ·  {summary}"
                    ),
                    halign="left",
                    valign="middle",
                ),
                "quiet",
            )
            edit.bind(
                size=lambda widget, size: setattr(
                    widget, "text_size", (size[0] - dp(18), size[1])
                )
            )
            if phase.status is PhaseStatus.BLOCKED:
                edit.color = RED
            up = style_button(
                Button(text="Up", size_hint_x=None, width=dp(46)), "secondary"
            )
            down = style_button(
                Button(text="Down", size_hint_x=None, width=dp(52)), "secondary"
            )
            remove = style_button(
                Button(text="Del", size_hint_x=None, width=dp(46)), "danger"
            )
            todos = style_button(
                Button(text="To-Dos", size_hint_x=None, width=dp(82)), "secondary"
            )
            edit.bind(on_release=partial(self._edit, phase))
            up.bind(on_release=partial(self._move, phase.id, -1))
            down.bind(on_release=partial(self._move, phase.id, 1))
            remove.bind(on_release=partial(self._remove, phase.id))
            todos.bind(on_release=partial(self._open_todos, phase))
            row.add_widget(edit)
            row.add_widget(todos)
            row.add_widget(up)
            row.add_widget(down)
            row.add_widget(remove)
            self._rows.add_widget(row)

    def _add(self, *_: object) -> None:
        if self._project_id is None:
            return
        PhaseEditorPopup(None, self._add_phase).open()

    def _add_phase(
        self, name: str, description: str, status: PhaseStatus
    ) -> None:
        if self._project_id is not None:
            self._phases.add(self._project_id, name, description, status)
            self.refresh()

    def _edit(self, phase: Phase, *_: object) -> None:
        if self._project_id is None:
            return

        def submit(name: str, description: str, status: PhaseStatus) -> None:
            if self._project_id is not None:
                self._phases.update(
                    phase.id,
                    self._project_id,
                    name,
                    description,
                    status,
                )
                self.refresh()

        PhaseEditorPopup(phase, submit).open()

    def _move(self, phase_id: str, offset: int, *_: object) -> None:
        if self._project_id is not None:
            self._phases.move(self._project_id, phase_id, offset)
            self.refresh()

    def _remove(self, phase_id: str, *_: object) -> None:
        if self._project_id is not None:
            self._phases.remove(self._project_id, phase_id)
            self.refresh()

    def _reset(self, *_: object) -> None:
        if self._project_id is not None:
            self._workflows.reset_phase_plan(self._project_id)
            self.refresh()

    def _open_todos(self, phase: Phase, *_: object) -> None:
        if self._project_id is not None:
            TodoManagerPopup(
                self._todos,
                self._project_id,
                TodoModule.PHASES,
                f"To-Dos · {phase.name}",
                phase.id,
            ).open()
