from collections.abc import Sequence
from typing import Protocol

from project_planner.core.domain.phases.phase import Phase


class PhasePlanStrategy(Protocol):
    def create(self, project_id: str) -> Sequence[Phase]: ...
