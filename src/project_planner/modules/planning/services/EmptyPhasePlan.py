from collections.abc import Sequence

from project_planner.modules.planning.entities.Phase import Phase


class EmptyPhasePlan:
    def create(self, project_id: str) -> Sequence[Phase]:
        return []
