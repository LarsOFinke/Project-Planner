from collections.abc import Sequence
from typing import Protocol

from project_planner.modules.planning.entities.Phase import Phase


class PhasePlanStrategy(Protocol):
    def create(self, project_id: str) -> Sequence[Phase]: ...
