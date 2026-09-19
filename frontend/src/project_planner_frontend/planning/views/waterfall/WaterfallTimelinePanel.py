from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView

from project_planner.modules.planning.entities.Phase import Phase
from project_planner_frontend.planning.clients.PhaseClient import PhaseClient
from project_planner_frontend.planning.clients.WaterfallTaskClient import WaterfallTaskClient
from project_planner_frontend.shared.date_parser import format_optional_date
from project_planner_frontend.shared.theme import (
    NAVY_900,
    PEARL_GREY,
    SLATE_400,
    paint_background,
    section_label,
)


class WaterfallTimelinePanel(BoxLayout):
    def __init__(self, phases: PhaseClient, tasks: WaterfallTaskClient, **kwargs: object) -> None:
        super().__init__(orientation="vertical", **kwargs)
        self._phases = phases
        self._tasks = tasks
        self._project_id: str | None = None
        self._section_id: str | None = None
        paint_background(self, NAVY_900)
        self._rows = BoxLayout(
            orientation="vertical", size_hint_y=None, spacing=dp(7), padding=dp(10)
        )
        self._rows.bind(minimum_height=self._rows.setter("height"))
        scroll = ScrollView(do_scroll_x=False)
        scroll.add_widget(self._rows)
        self.add_widget(scroll)

    def show_context(self, project_id: str, section_id: str | None = None) -> None:
        self._project_id = project_id
        self._section_id = section_id
        self.refresh()

    def refresh(self) -> None:
        self._rows.clear_widgets()
        if self._project_id is None:
            return
        phases = sorted(
            self._phases.list_for_context(self._project_id, self._section_id),
            key=lambda phase: (phase.start_date is None, phase.start_date, phase.position),
        )
        if not phases:
            self._rows.add_widget(
                Label(
                    text="No timeline entries yet.",
                    color=SLATE_400,
                    size_hint_y=None,
                    height=dp(54),
                )
            )
        lanes: dict[str | None, list[Phase]] = {}
        for phase in phases:
            lanes.setdefault(phase.parallel_group, []).append(phase)
        for parallel_group, lane in lanes.items():
            if parallel_group is not None:
                self._rows.add_widget(
                    section_label(f"Parallel work · {parallel_group} ({len(lane)} phases)")
                )
            for phase in lane:
                self._add_phase(phase, parallel_group is not None)

    def _add_phase(self, phase: Phase, parallel: bool) -> None:
        tasks = list(self._tasks.list_for_phase(phase.id))
        task_names = ", ".join(task.title for task in tasks) or "No tasks"
        start = format_optional_date(phase.start_date) or "No start"
        end = format_optional_date(phase.end_date) or "No end"
        self._rows.add_widget(
            Label(
                text=(
                    f"{'↳ ' if parallel else ''}{phase.name}  ·  {start} → {end}\n"
                    f"Tasks: {task_names}"
                ),
                color=PEARL_GREY,
                halign="left",
                valign="middle",
                size_hint_y=None,
                height=dp(64),
            )
        )
