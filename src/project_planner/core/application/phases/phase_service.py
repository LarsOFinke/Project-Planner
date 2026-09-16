from collections.abc import Sequence

from project_planner.core.application.planning.phase_plan_factory import build_phase_plan
from project_planner.core.domain.phases.phase import Phase
from project_planner.core.domain.projects.planning_method import PlanningMethod
from project_planner.core.ports.phase_repository import PhaseRepository


class PhaseService:
    def __init__(self, phases: PhaseRepository) -> None:
        self._phases = phases

    def initialize(self, project_id: str, method: PlanningMethod) -> Sequence[Phase]:
        phases = build_phase_plan(method, project_id)
        self._phases.save_all(project_id, phases)
        return phases

    def list_for_project(self, project_id: str) -> Sequence[Phase]:
        return self._phases.list_for_project(project_id)

    def add(self, project_id: str, name: str, description: str = "") -> Phase:
        phases = list(self.list_for_project(project_id))
        phase = Phase(project_id, name.strip(), len(phases), description.strip())
        phases.append(phase)
        self._phases.save_all(project_id, phases)
        return phase

    def update(self, phase_id: str, project_id: str, name: str, description: str) -> Phase:
        phases = list(self.list_for_project(project_id))
        index = self._index_of(phases, phase_id)
        phases[index] = phases[index].revise(
            name=name.strip(), description=description.strip()
        )
        self._phases.save_all(project_id, phases)
        return phases[index]

    def remove(self, project_id: str, phase_id: str) -> None:
        phases = [
            phase for phase in self.list_for_project(project_id) if phase.id != phase_id
        ]
        normalized = [phase.revise(position=index) for index, phase in enumerate(phases)]
        self._phases.save_all(project_id, normalized)

    def move(self, project_id: str, phase_id: str, offset: int) -> None:
        phases = list(self.list_for_project(project_id))
        source = self._index_of(phases, phase_id)
        target = max(0, min(len(phases) - 1, source + offset))
        phases.insert(target, phases.pop(source))
        normalized = [phase.revise(position=index) for index, phase in enumerate(phases)]
        self._phases.save_all(project_id, normalized)

    @staticmethod
    def _index_of(phases: Sequence[Phase], phase_id: str) -> int:
        for index, phase in enumerate(phases):
            if phase.id == phase_id:
                return index
        raise LookupError(f"Phase {phase_id!r} does not exist")
