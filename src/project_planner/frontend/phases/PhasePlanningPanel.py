from datetime import date
from functools import partial

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView

from project_planner.core.application.phases.PhaseService import PhaseService
from project_planner.core.application.projects.ProjectWorkflowService import (
    ProjectWorkflowService,
)
from project_planner.core.application.todos.TodoService import TodoService
from project_planner.core.application.waterfall.WaterfallTaskService import WaterfallTaskService
from project_planner.core.domain.phases.Phase import Phase
from project_planner.core.domain.phases.PhaseStatus import PhaseStatus
from project_planner.core.domain.todos.TodoModule import TodoModule
from project_planner.frontend.phases.PhaseEditorPopup import PhaseEditorPopup
from project_planner.frontend.planning.waterfall.WaterfallTasksPopup import WaterfallTasksPopup
from project_planner.frontend.shared.date_parser import format_optional_date
from project_planner.frontend.shared.theme import (
    NAVY_900,
    caption_label,
    empty_state_label,
    paint_background,
    section_label,
    style_button,
    title_label,
)
from project_planner.frontend.todos.TodoManagerPopup import TodoManagerPopup


class PhasePlanningPanel(BoxLayout):
    def __init__(
        self,
        phases: PhaseService,
        workflows: ProjectWorkflowService,
        tasks: WaterfallTaskService,
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
        self._tasks = tasks
        self._todos = todos
        self._project_id: str | None = None
        self._section_id: str | None = None
        paint_background(self, NAVY_900)
        self.add_widget(title_label("Waterfall plan"))
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
        self.add_widget(section_label("Ordered delivery phases"))
        self._rows = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(5))
        self._rows.bind(minimum_height=self._rows.setter("height"))
        scroll = ScrollView(do_scroll_x=False, bar_width=dp(5))
        scroll.add_widget(self._rows)
        self.add_widget(controls)
        self.add_widget(scroll)
        self.disabled = True

    def show_project(self, project_id: str) -> None:
        self.show_context(project_id)

    def show_context(self, project_id: str, section_id: str | None = None) -> None:
        self._project_id = project_id
        self._section_id = section_id
        self.disabled = False
        self.refresh()

    def refresh(self) -> None:
        self._rows.clear_widgets()
        if self._project_id is None:
            return
        phases = self._phases.list_for_context(self._project_id, self._section_id)
        if not phases:
            self._rows.add_widget(
                empty_state_label(
                    "No phases yet. Add one or load the selected planning template."
                )
            )
            return
        for phase in phases:
            row = BoxLayout(
                size_hint_y=None,
                height=dp(78),
                spacing=dp(6),
                padding=[dp(14), 0, 0, 0],
            )
            summary = phase.description.strip() or "No description"
            phase_tasks = list(self._tasks.list_for_phase(phase.id))
            task_summary = ", ".join(task.title for task in phase_tasks) or "No tasks"
            edit = style_button(
                Button(
                    text=(
                        f"{phase.name}\n"
                        f"{phase.status.value.replace('_', ' ').title()} · "
                        f"{format_optional_date(phase.start_date) or 'No start'} → "
                        f"{format_optional_date(phase.end_date) or 'No end'} · {summary}\n"
                        f"Tasks: {task_summary}"
                    ),
                    halign="left",
                    valign="middle",
                ),
                "quiet",
            )
            edit.bind(
                size=lambda widget, size: setattr(widget, "text_size", (size[0] - dp(18), size[1]))
            )
            up = style_button(Button(text="Up", size_hint_x=None, width=dp(46)), "secondary")
            down = style_button(Button(text="Down", size_hint_x=None, width=dp(52)), "secondary")
            remove = style_button(Button(text="Delete", size_hint_x=None, width=dp(76)), "danger")
            todos = style_button(Button(text="To-Dos", size_hint_x=None, width=dp(82)), "secondary")
            task_count = len(phase_tasks)
            tasks = style_button(
                Button(text=f"Tasks ({task_count})", size_hint_x=None, width=dp(104)),
                "secondary",
            )
            edit.bind(on_release=partial(self._edit, phase))
            up.bind(on_release=partial(self._move, phase.id, -1))
            down.bind(on_release=partial(self._move, phase.id, 1))
            remove.bind(on_release=partial(self._remove, phase.id))
            todos.bind(on_release=partial(self._open_todos, phase))
            tasks.bind(on_release=partial(self._open_tasks, phase))
            row.add_widget(edit)
            row.add_widget(tasks)
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
        self,
        name: str,
        description: str,
        status: PhaseStatus,
        start_date: date | None,
        end_date: date | None,
    ) -> None:
        if self._project_id is not None:
            self._phases.add(
                self._project_id,
                name,
                description,
                status,
                start_date,
                end_date,
                self._section_id,
            )
            self.refresh()

    def _edit(self, phase: Phase, *_: object) -> None:
        if self._project_id is None:
            return

        def submit(
            name: str,
            description: str,
            status: PhaseStatus,
            start_date: date | None,
            end_date: date | None,
        ) -> None:
            if self._project_id is not None:
                self._phases.update(
                    phase.id,
                    self._project_id,
                    name,
                    description,
                    status,
                    start_date,
                    end_date,
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
            if self._section_id is None:
                self._workflows.reset_phase_plan(self._project_id)
            else:
                self._phases.reset_waterfall(self._project_id, self._section_id)
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

    def _open_tasks(self, phase: Phase, *_: object) -> None:
        WaterfallTasksPopup(self._tasks, phase, self.refresh).open()
