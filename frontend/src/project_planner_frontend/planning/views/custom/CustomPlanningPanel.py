from datetime import date
from functools import partial

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView

from project_planner.modules.planning.entities.PlanningSection import PlanningSection
from project_planner.modules.planning.entities.SectionStatus import SectionStatus
from project_planner.modules.planning.entities.SectionType import SectionType
from project_planner_frontend.collaboration.clients.TodoClient import TodoClient
from project_planner_frontend.planning.clients.AgileClient import AgileClient
from project_planner_frontend.planning.clients.PhaseClient import PhaseClient
from project_planner_frontend.planning.clients.SectionClient import SectionClient
from project_planner_frontend.planning.clients.WaterfallTaskClient import WaterfallTaskClient
from project_planner_frontend.planning.views.custom.SectionEditorPopup import SectionEditorPopup
from project_planner_frontend.planning.views.custom.SectionPlanningPopup import SectionPlanningPopup
from project_planner_frontend.projects.clients.ProjectWorkflowClient import ProjectWorkflowClient
from project_planner_frontend.shared.date_parser import format_optional_date
from project_planner_frontend.shared.theme import (
    NAVY_900,
    caption_label,
    empty_state_label,
    paint_background,
    section_label,
    style_button,
    title_label,
)


class CustomPlanningPanel(BoxLayout):
    def __init__(
        self,
        sections: SectionClient,
        agile: AgileClient,
        phases: PhaseClient,
        workflows: ProjectWorkflowClient,
        tasks: WaterfallTaskClient,
        todos: TodoClient,
        **kwargs: object,
    ) -> None:
        super().__init__(orientation="vertical", spacing=dp(8), padding=dp(8), **kwargs)
        self._sections = sections
        self._agile = agile
        self._phases = phases
        self._workflows = workflows
        self._tasks = tasks
        self._todos = todos
        self._project_id: str | None = None
        paint_background(self, NAVY_900)
        self.add_widget(title_label("Custom roadmap"))
        self.add_widget(
            caption_label(
                "Keep every section in its intended order, including completed roadmap steps."
            )
        )
        controls = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(6))
        for section_type in SectionType:
            button = style_button(
                Button(text=f"+ {section_type.value.title()} section"),
                "primary" if section_type is SectionType.FREE else "secondary",
            )
            button.bind(on_release=partial(self._add, section_type))
            controls.add_widget(button)
        self.add_widget(controls)
        self.add_widget(section_label("Ordered roadmap sections"))
        self._roadmap_rows = self._rows()
        self.add_widget(self._roadmap_rows[0])

    def show_project(self, project_id: str) -> None:
        self._project_id = project_id
        self.refresh()

    def refresh(self) -> None:
        self._roadmap_rows[1].clear_widgets()
        if self._project_id is None:
            return
        sections = list(self._sections.list_for_project(self._project_id))
        self._render(sections, self._roadmap_rows[1], True)

    def _render(self, sections: list[PlanningSection], rows: BoxLayout, reorder: bool) -> None:
        if not sections:
            rows.add_widget(empty_state_label("No roadmap sections yet."))
        for section in sections:
            row = BoxLayout(
                size_hint_y=None,
                height=dp(68),
                spacing=dp(5),
                padding=[dp(14), 0, 0, 0],
            )
            status = section.status.value.replace("_", " ").title()
            start = format_optional_date(section.start_date) or "No start"
            end = format_optional_date(section.end_date) or "No end"
            open_button = style_button(
                Button(
                    text=(
                        f"{section.position + 1}. {section.name}\n"
                        f"{section.section_type.value.title()} · {status} · {start} → {end}"
                    ),
                    halign="left",
                ),
                "quiet",
            )
            open_button.bind(on_release=partial(self._open, section))
            edit = style_button(Button(text="Edit", size_hint_x=None, width=dp(62)), "secondary")
            edit.bind(on_release=partial(self._edit, section))
            row.add_widget(open_button)
            row.add_widget(edit)
            if reorder:
                for label, offset in (("Up", -1), ("Down", 1)):
                    button = style_button(
                        Button(text=label, size_hint_x=None, width=dp(60)), "secondary"
                    )
                    button.bind(on_release=partial(self._move, section.id, offset))
                    row.add_widget(button)
            remove = style_button(Button(text="Delete", size_hint_x=None, width=dp(76)), "danger")
            remove.bind(on_release=partial(self._remove, section.id))
            row.add_widget(remove)
            rows.add_widget(row)

    def _add(self, section_type: SectionType, *_: object) -> None:
        SectionEditorPopup(None, section_type, self._create).open()

    def _create(
        self,
        name: str,
        description: str,
        section_type: SectionType,
        start_date: date | None,
        end_date: date | None,
        _status: SectionStatus,
    ) -> None:
        if self._project_id:
            self._sections.add(
                self._project_id, name, section_type, description, start_date, end_date
            )
            self.refresh()

    def _edit(self, section: PlanningSection, *_: object) -> None:
        def save(
            name: str,
            description: str,
            section_type: SectionType,
            start_date: date | None,
            end_date: date | None,
            status: SectionStatus,
        ) -> None:
            self._sections.update(
                section.id,
                name=name,
                description=description,
                section_type=section_type,
                start_date=start_date,
                end_date=end_date,
                status=status,
            )
            self.refresh()

        SectionEditorPopup(section, section.section_type, save).open()

    def _open(self, section: PlanningSection, *_: object) -> None:
        SectionPlanningPopup(
            section,
            self._sections,
            self._agile,
            self._phases,
            self._workflows,
            self._tasks,
            self._todos,
        ).open()

    def _move(self, section_id: str, offset: int, *_: object) -> None:
        if self._project_id:
            self._sections.move(self._project_id, section_id, offset)
            self.refresh()

    def _remove(self, section_id: str, *_: object) -> None:
        self._sections.remove(section_id)
        self.refresh()

    @staticmethod
    def _rows() -> tuple[ScrollView, BoxLayout]:
        rows = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(6), padding=dp(8))
        rows.bind(minimum_height=rows.setter("height"))
        scroll = ScrollView(do_scroll_x=False)
        scroll.add_widget(rows)
        return scroll, rows
