from kivy.core.window import Window
from kivy.uix.popup import Popup

from project_planner.core.application.agile.AgilePlanningService import AgilePlanningService
from project_planner.core.application.custom.SectionService import SectionService
from project_planner.core.application.phases.PhaseService import PhaseService
from project_planner.core.application.projects.ProjectWorkflowService import ProjectWorkflowService
from project_planner.core.application.todos.TodoService import TodoService
from project_planner.core.application.waterfall.WaterfallTaskService import WaterfallTaskService
from project_planner.core.domain.custom.PlanningSection import PlanningSection
from project_planner.core.domain.custom.SectionType import SectionType
from project_planner.frontend.planning.agile.AgilePlanningPanel import AgilePlanningPanel
from project_planner.frontend.planning.custom.FreeSectionPanel import FreeSectionPanel
from project_planner.frontend.planning.waterfall.WaterfallPlanningPanel import (
    WaterfallPlanningPanel,
)
from project_planner.frontend.shared.theme import GOLD, NAVY_800, PEARL_GREY


class SectionPlanningPopup(Popup):
    def __init__(
        self,
        section: PlanningSection,
        sections: SectionService,
        agile: AgilePlanningService,
        phases: PhaseService,
        workflows: ProjectWorkflowService,
        tasks: WaterfallTaskService,
        todos: TodoService,
        **kwargs: object,
    ) -> None:
        if section.section_type is SectionType.AGILE:
            content = AgilePlanningPanel(agile)
            content.show_context(section.project_id, section.id)
        elif section.section_type is SectionType.WATERFALL:
            content = WaterfallPlanningPanel(phases, workflows, tasks, todos)
            content.show_context(section.project_id, section.id)
        else:
            content = FreeSectionPanel(sections)
            content.show_section(section.id)
        super().__init__(
            title=f"{section.name} · {section.section_type.value.title()}",
            title_color=PEARL_GREY,
            separator_color=GOLD,
            background_color=NAVY_800,
            content=content,
            size_hint=(None, None),
            width=Window.width * 0.96,
            height=Window.height * 0.94,
            **kwargs,
        )
