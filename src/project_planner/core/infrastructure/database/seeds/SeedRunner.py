from collections.abc import Sequence

from sqlalchemy import select

from project_planner.core.domain.shared.clock import utc_now
from project_planner.core.infrastructure.database.Database import Database
from project_planner.core.infrastructure.database.models.SeedRecordModel import SeedRecordModel
from project_planner.core.infrastructure.database.seeds.Seed import Seed


class SeedRunner:
    def __init__(self, database: Database, seeds: Sequence[Seed] = ()) -> None:
        self._database = database
        self._seeds = seeds

    def run(self) -> None:
        with self._database.session() as session:
            applied = set(session.scalars(select(SeedRecordModel.key)))
            for seed in self._seeds:
                if seed.key in applied:
                    continue
                seed.apply(session)
                session.add(SeedRecordModel(key=seed.key, applied_at=utc_now()))
