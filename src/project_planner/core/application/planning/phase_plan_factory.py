from collections.abc import Sequence

from project_planner.core.application.planning.empty_phase_plan import EmptyPhasePlan
from project_planner.core.application.planning.named_phase_plan import NamedPhasePlan
from project_planner.core.application.planning.phase_plan_strategy import PhasePlanStrategy
from project_planner.core.domain.phases.phase import Phase
from project_planner.core.domain.projects.planning_method import PlanningMethod

_STRATEGIES: dict[PlanningMethod, PhasePlanStrategy] = {
    PlanningMethod.WATERFALL: NamedPhasePlan(
        ("Requirements", "Design", "Implementation", "Verification", "Deployment")
    ),
    PlanningMethod.AGILE: NamedPhasePlan(
        ("Product discovery", "Backlog", "Iteration", "Review", "Retrospective")
    ),
    PlanningMethod.CUSTOM: EmptyPhasePlan(),
}


def build_phase_plan(method: PlanningMethod, project_id: str) -> Sequence[Phase]:
    return _STRATEGIES[method].create(project_id)
