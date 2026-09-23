from datetime import date
from functools import partial

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView

from project_planner.modules.planning.entities.Phase import Phase
from project_planner.modules.planning.entities.PhaseStatus import PhaseStatus
from project_planner.modules.planning.entities.WaterfallTask import WaterfallTask
from project_planner.modules.todos.entities.TodoModule import TodoModule
from project_planner_frontend.collaboration.clients.TodoClient import TodoClient
from project_planner_frontend.collaboration.views.todos.TodoManagerPopup import TodoManagerPopup
from project_planner_frontend.planning.clients.PhaseClient import PhaseClient
from project_planner_frontend.planning.clients.WaterfallTaskClient import WaterfallTaskClient
from project_planner_frontend.planning.views.waterfall.PhaseEditorPopup import PhaseEditorPopup
from project_planner_frontend.planning.views.waterfall.WaterfallTasksPopup import (
    WaterfallTasksPopup,
)
from project_planner_frontend.projects.clients.ProjectWorkflowClient import (
    ProjectWorkflowClient,
)
from project_planner_frontend.shared.date_parser import format_optional_date
from project_planner_frontend.shared.ReorderableRow import ReorderableRow
from project_planner_frontend.shared.theme import (
    NAVY_900,
    caption_label,
    empty_state_label,
    paint_background,
    section_label,
    style_button,
    title_label,
)


class PhasePlanningPanel(BoxLayout):
    def __init__(
        self,
        phases: PhaseClient,
        workflows: ProjectWorkflowClient,
        tasks: WaterfallTaskClient,
        todos: TodoClient,
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
        self._drop_target_row: ReorderableRow | None = None
        paint_background(self, NAVY_900)
        self.add_widget(title_label("Waterfall plan"))
        self.add_widget(caption_label("Drag a phase onto another to change the delivery order."))
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
        self._scroll = ScrollView(do_scroll_x=False, bar_width=dp(5))
        self._scroll.add_widget(self._rows)
        self.add_widget(controls)
        self.add_widget(self._scroll)
        self.disabled = True

    def show_project(self, project_id: str) -> None:
        self.show_context(project_id)

    def show_context(self, project_id: str, section_id: str | None = None) -> None:
        self._project_id = project_id
        self._section_id = section_id
        self.disabled = False
        self.refresh()

    def refresh(self) -> None:
        self._clear_drop_target()
        self._rows.clear_widgets()
        if self._project_id is None:
            return
        phases = self._phases.list_for_context(self._project_id, self._section_id)
        self._render_phases(phases)

    def show_fetched(
        self,
        project_id: str,
        section_id: str | None,
        phases: list[Phase],
        tasks_by_phase: dict[str, list[WaterfallTask]],
    ) -> None:
        self._project_id = project_id
        self._section_id = section_id
        self.disabled = False
        self._clear_drop_target()
        self._rows.clear_widgets()
        self._render_phases(phases, tasks_by_phase)

    def _render_phases(
        self,
        phases: list[Phase],
        tasks_by_phase: dict[str, list[WaterfallTask]] | None = None,
    ) -> None:
        if not phases:
            self._rows.add_widget(
                empty_state_label("No phases yet. Add one or load the selected planning template.")
            )
            return
        for phase in phases:
            row = ReorderableRow(
                phase.id,
                partial(self._edit, phase),
                self._drag_phase,
                self._drop_phase,
                size_hint_y=None,
                height=dp(78),
                spacing=dp(6),
                padding=[dp(14), 0, 0, 0],
            )
            summary = phase.description.strip() or "No description"
            phase_tasks = (
                tasks_by_phase[phase.id]
                if tasks_by_phase is not None
                else list(self._tasks.list_for_phase(phase.id))
            )
            task_summary = ", ".join(task.title for task in phase_tasks) or "No tasks"
            parallel = (
                f" · Parallel: {phase.parallel_group}" if phase.parallel_group is not None else ""
            )
            edit = style_button(
                Button(
                    text=(
                        f"{phase.name}\n"
                        f"{phase.status.value.replace('_', ' ').title()} · "
                        f"{format_optional_date(phase.start_date) or 'No start'} → "
                        f"{format_optional_date(phase.end_date) or 'No end'} · {summary}\n"
                        f"Tasks: {task_summary}{parallel}"
                    ),
                    halign="left",
                    valign="middle",
                ),
                "quiet",
            )
            edit.bind(
                size=lambda widget, size: setattr(widget, "text_size", (size[0] - dp(18), size[1]))
            )
            remove = style_button(Button(text="Delete", size_hint_x=None, width=dp(76)), "danger")
            todos = style_button(Button(text="To-Dos", size_hint_x=None, width=dp(82)), "secondary")
            task_count = len(phase_tasks)
            tasks = style_button(
                Button(text=f"Tasks ({task_count})", size_hint_x=None, width=dp(104)),
                "secondary",
            )
            remove.bind(on_release=partial(self._remove, phase.id))
            todos.bind(on_release=partial(self._open_todos, phase))
            tasks.bind(on_release=partial(self._open_tasks, phase))
            row.add_widget(edit)
            row.add_widget(tasks)
            row.add_widget(todos)
            row.add_widget(remove)
            row.set_primary_control(edit)
            row.register_action_controls((tasks, todos, remove))
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
        parallel_group: str | None,
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
                parallel_group,
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
            parallel_group: str | None,
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
                    parallel_group,
                )
                self.refresh()

        PhaseEditorPopup(phase, submit).open()

    def _drag_phase(self, phase_id: str, position: tuple[float, float] | None) -> None:
        target = None if position is None else self._drop_target_at(phase_id, position)
        if target is self._drop_target_row:
            return
        self._clear_drop_target()
        self._drop_target_row = target
        if target is not None:
            target.set_drop_target(True)

    def _drop_phase(self, phase_id: str, position: tuple[float, float]) -> None:
        target = self._drop_target_at(phase_id, position)
        self._clear_drop_target()
        if target is not None and self._project_id is not None:
            self._phases.move_to(self._project_id, phase_id, target.item_id)
            self.refresh()

    def _drop_target_at(
        self, phase_id: str, position: tuple[float, float]
    ) -> ReorderableRow | None:
        if not self._scroll.collide_point(*position):
            return None
        list_position = self._rows.to_widget(*position)
        return next(
            (
                row
                for row in self._rows.children
                if isinstance(row, ReorderableRow)
                and row.item_id != phase_id
                and row.collide_point(*list_position)
            ),
            None,
        )

    def _clear_drop_target(self) -> None:
        if self._drop_target_row is not None:
            self._drop_target_row.set_drop_target(False)
        self._drop_target_row = None

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
