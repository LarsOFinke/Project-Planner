from collections.abc import Sequence
from datetime import date

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

    def list_for_context(self, project_id: str, section_id: str | None = None) -> Sequence[Phase]:
        return [
            phase for phase in self.list_for_project(project_id) if phase.section_id == section_id
        ]

    def initialize_waterfall(
        self, project_id: str, section_id: str | None = None
    ) -> Sequence[Phase]:
        existing = list(self.list_for_project(project_id))
        if any(phase.section_id == section_id for phase in existing):
            return self.list_for_context(project_id, section_id)
        names = ("Planning", "Design", "Execution", "Completion")
        created = [
            Phase(
                project_id=project_id,
                name=name,
                position=len(existing) + index,
                section_id=section_id,
            )
            for index, name in enumerate(names)
        ]
        self._phases.save_all(project_id, [*existing, *created])
        return created

    def reset_waterfall(self, project_id: str, section_id: str | None = None) -> Sequence[Phase]:
        retained = [
            phase for phase in self.list_for_project(project_id) if phase.section_id != section_id
        ]
        self._phases.save_all(project_id, self._normalize_positions(retained))
        return self.initialize_waterfall(project_id, section_id)

    def add(
        self,
        project_id: str,
        name: str,
        description: str = "",
        status: PhaseStatus = PhaseStatus.NOT_STARTED,
        start_date: date | None = None,
        end_date: date | None = None,
        section_id: str | None = None,
    ) -> Phase:
        phases = list(self.list_for_project(project_id))
        phase = Phase(
            project_id,
            name.strip(),
            position=len(phases),
            description=description.strip(),
            status=status,
            start_date=start_date,
            end_date=end_date,
            section_id=section_id,
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
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> Phase:
        phases = list(self.list_for_project(project_id))
        index = self._index_of(phases, phase_id)
        changes: dict[str, object] = {
            "name": name.strip(),
            "description": description.strip(),
            "start_date": start_date,
            "end_date": end_date,
        }
        if status is not None:
            changes["status"] = status
        phases[index] = phases[index].revise(**changes)
        self._phases.save_all(project_id, phases)
        return phases[index]

    def remove(self, project_id: str, phase_id: str) -> None:
        phases = [phase for phase in self.list_for_project(project_id) if phase.id != phase_id]
        normalized = self._normalize_positions(phases)
        self._phases.save_all(project_id, normalized)

    def move(self, project_id: str, phase_id: str, offset: int) -> None:
        phases = list(self.list_for_project(project_id))
        source = self._index_of(phases, phase_id)
        context = phases[source].section_id
        context_indexes = [
            index for index, phase in enumerate(phases) if phase.section_id == context
        ]
        context_position = context_indexes.index(source)
        target_position = max(0, min(len(context_indexes) - 1, context_position + offset))
        target = context_indexes[target_position]
        phases[source], phases[target] = phases[target], phases[source]
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
