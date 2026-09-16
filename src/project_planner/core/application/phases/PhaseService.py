from collections.abc import Sequence

from project_planner.core.application.planning.phase_plan_factory import build_phase_plan
from project_planner.core.domain.phases.Phase import Phase
from project_planner.core.domain.phases.PhaseStatus import PhaseStatus
from project_planner.core.domain.projects.PlanningMethod import PlanningMethod
from project_planner.core.ports.PhaseRepository import PhaseRepository


class PhaseService:
    def __init__(self, phases: PhaseRepository) -> None:
        self._phases = phases

    def initialize(self, project_id: str, method: PlanningMethod) -> Sequence[Phase]:
        phases = build_phase_plan(method, project_id)
        self._phases.save_all(project_id, phases)
        return phases

    def list_for_project(self, project_id: str) -> Sequence[Phase]:
        return self._phases.list_for_project(project_id)

    def add(
        self,
        project_id: str,
        name: str,
        description: str = "",
        status: PhaseStatus = PhaseStatus.PLANNED,
    ) -> Phase:
        phases = list(self.list_for_project(project_id))
        phase = Phase(
            project_id,
            name.strip(),
            len(phases),
            description.strip(),
            status,
        )
        phases.append(phase)
        self._phases.save_all(project_id, phases)
        return phase

    def update(
        self,
        phase_id: str,
        project_id: str,
        name: str,
        description: str,
        status: PhaseStatus | None = None,
    ) -> Phase:
        phases = list(self.list_for_project(project_id))
        index = self._index_of(phases, phase_id)
        changes: dict[str, object] = {
            "name": name.strip(),
            "description": description.strip(),
        }
        if status is not None:
            changes["status"] = status
        phases[index] = phases[index].revise(**changes)
        self._phases.save_all(project_id, phases)
        return phases[index]

    def remove(self, project_id: str, phase_id: str) -> None:
        phases = [
            phase for phase in self.list_for_project(project_id) if phase.id != phase_id
        ]
        normalized = self._normalize_positions(phases)
        self._phases.save_all(project_id, normalized)

    def move(self, project_id: str, phase_id: str, offset: int) -> None:
        phases = list(self.list_for_project(project_id))
        source = self._index_of(phases, phase_id)
        target = max(0, min(len(phases) - 1, source + offset))
        phases.insert(target, phases.pop(source))
        normalized = self._normalize_positions(phases)
        self._phases.save_all(project_id, normalized)

    @staticmethod
    def _normalize_positions(phases: Sequence[Phase]) -> list[Phase]:
        return [
            phase if phase.position == index else phase.revise(position=index)
            for index, phase in enumerate(phases)
        ]

    @staticmethod
    def _index_of(phases: Sequence[Phase], phase_id: str) -> int:
        for index, phase in enumerate(phases):
            if phase.id == phase_id:
                return index
        raise LookupError(f"Phase {phase_id!r} does not exist")
