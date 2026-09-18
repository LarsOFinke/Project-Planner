from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
from uuid import uuid4

from project_planner.modules.resources.entities.ResourceLinkKind import ResourceLinkKind
from project_planner.shared.utils.clock import utc_now


@dataclass(frozen=True, slots=True)
class ResourceLink:
    project_id: str
    title: str
    target: str
    kind: ResourceLinkKind
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise ValueError("Link title must not be empty")
        if self.kind is ResourceLinkKind.WEB:
            parsed = urlparse(self.target)
            if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                raise ValueError("Web links must use a valid http:// or https:// URL")
        elif not Path(self.target).expanduser().is_absolute():
            raise ValueError("File links must use an absolute path")

    def revise(self, **changes: object) -> ResourceLink:
        return replace(self, **changes, updated_at=utc_now())
