from collections.abc import Sequence

from project_planner.core.domain.phases.Phase import Phase


class EmptyPhasePlan:
    def create(self, project_id: str) -> Sequence[Phase]:
        return []
