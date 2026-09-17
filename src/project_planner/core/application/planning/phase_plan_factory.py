from collections.abc import Sequence

from project_planner.core.application.planning.EmptyPhasePlan import EmptyPhasePlan
from project_planner.core.application.planning.NamedPhasePlan import NamedPhasePlan
from project_planner.core.application.planning.PhasePlanStrategy import PhasePlanStrategy
from project_planner.core.domain.phases.Phase import Phase
from project_planner.core.domain.projects.PlanningMethod import PlanningMethod

_STRATEGIES: dict[PlanningMethod, PhasePlanStrategy] = {
    PlanningMethod.WATERFALL: NamedPhasePlan(("Planning", "Design", "Execution", "Completion")),
    PlanningMethod.AGILE: EmptyPhasePlan(),
    PlanningMethod.CUSTOM: EmptyPhasePlan(),
}


def build_phase_plan(method: PlanningMethod, project_id: str) -> Sequence[Phase]:
    return _STRATEGIES[method].create(project_id)
