from collections.abc import Sequence
from typing import Protocol

from project_planner.core.domain.phases.phase import Phase


class PhaseRepository(Protocol):
    def save_all(self, project_id: str, phases: Sequence[Phase]) -> None: ...
    def list_for_project(self, project_id: str) -> Sequence[Phase]: ...
