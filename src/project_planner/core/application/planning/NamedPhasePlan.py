from collections.abc import Sequence
from dataclasses import dataclass

from project_planner.core.domain.phases.Phase import Phase


@dataclass(frozen=True)
class NamedPhasePlan:
    names: tuple[str, ...]

    def create(self, project_id: str) -> Sequence[Phase]:
        return [
            Phase(project_id=project_id, name=name, position=index)
            for index, name in enumerate(self.names)
        ]
