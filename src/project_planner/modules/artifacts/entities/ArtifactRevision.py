from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class ArtifactRevision:
    id: str
    artifact_id: str
    content: str
    created_at: datetime
