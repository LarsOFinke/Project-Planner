from collections.abc import Sequence

from project_planner.modules.planning.entities.Phase import Phase
from project_planner.modules.planning.protocols.PhasePlanStrategy import PhasePlanStrategy
from project_planner.modules.planning.services.EmptyPhasePlan import EmptyPhasePlan
from project_planner.modules.planning.services.NamedPhasePlan import NamedPhasePlan
from project_planner.modules.projects.entities.PlanningMethod import PlanningMethod

_STRATEGIES: dict[PlanningMethod, PhasePlanStrategy] = {
    PlanningMethod.WATERFALL: NamedPhasePlan(("Planning", "Design", "Execution", "Completion")),
    PlanningMethod.AGILE: EmptyPhasePlan(),
    PlanningMethod.CUSTOM: EmptyPhasePlan(),
}


def build_phase_plan(method: PlanningMethod, project_id: str) -> Sequence[Phase]:
    return _STRATEGIES[method].create(project_id)
