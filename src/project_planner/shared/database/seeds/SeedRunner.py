from collections.abc import Sequence

from sqlalchemy import select

from project_planner.shared.database.Database import Database
from project_planner.shared.database.models.SeedRecordModel import SeedRecordModel
from project_planner.shared.database.seeds.Seed import Seed
from project_planner.shared.utils.clock import utc_now


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
