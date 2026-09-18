from kivy.core.window import Window
from kivy.uix.popup import Popup

from project_planner.modules.planning.entities.PlanningSection import PlanningSection
from project_planner.modules.planning.entities.SectionType import SectionType
from project_planner_frontend.collaboration.clients.TodoClient import TodoClient
from project_planner_frontend.planning.clients.AgileClient import AgileClient
from project_planner_frontend.planning.clients.PhaseClient import PhaseClient
from project_planner_frontend.planning.clients.SectionClient import SectionClient
from project_planner_frontend.planning.clients.WaterfallTaskClient import WaterfallTaskClient
from project_planner_frontend.planning.views.agile.AgilePlanningPanel import AgilePlanningPanel
from project_planner_frontend.planning.views.custom.FreeSectionPanel import FreeSectionPanel
from project_planner_frontend.planning.views.waterfall.WaterfallPlanningPanel import (
    WaterfallPlanningPanel,
)
from project_planner_frontend.projects.clients.ProjectWorkflowClient import ProjectWorkflowClient
from project_planner_frontend.shared.theme import GOLD, NAVY_800, PEARL_GREY


class SectionPlanningPopup(Popup):
    def __init__(
        self,
        section: PlanningSection,
        sections: SectionClient,
        agile: AgileClient,
        phases: PhaseClient,
        workflows: ProjectWorkflowClient,
        tasks: WaterfallTaskClient,
        todos: TodoClient,
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
