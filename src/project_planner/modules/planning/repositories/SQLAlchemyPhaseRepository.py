from collections.abc import Sequence

from sqlalchemy import delete, select

from project_planner.modules.planning.entities.Phase import Phase
from project_planner.modules.planning.entities.PhaseStatus import PhaseStatus
from project_planner.shared.database.Database import Database
from project_planner.shared.database.models.PhaseModel import PhaseModel


class SQLAlchemyPhaseRepository:
    def __init__(self, database: Database) -> None:
        self._database = database

    def save_all(self, project_id: str, phases: Sequence[Phase]) -> None:
        with self._database.session() as session:
            existing = list(
                session.scalars(select(PhaseModel).where(PhaseModel.project_id == project_id))
            )
            retained_ids = {phase.id for phase in phases}
            for temporary_position, model in enumerate(existing, start=1):
                model.position = -temporary_position
            session.flush()
            session.execute(
                delete(PhaseModel).where(
                    PhaseModel.project_id == project_id,
                    PhaseModel.id.not_in(retained_ids),
                )
            )
            for phase in phases:
                session.merge(
                    PhaseModel(
                        id=phase.id,
                        project_id=phase.project_id,
                        name=phase.name,
                        description=phase.description,
                        status=phase.status.value,
                        position=phase.position,
                        start_date=phase.start_date,
                        end_date=phase.end_date,
                        section_id=phase.section_id,
                        parallel_group=phase.parallel_group,
                        created_at=phase.created_at,
                        updated_at=phase.updated_at,
                    )
                )

    def list_for_project(self, project_id: str) -> Sequence[Phase]:
        statement = (
            select(PhaseModel)
            .where(PhaseModel.project_id == project_id)
            .order_by(PhaseModel.position)
        )
        with self._database.session() as session:
            return [
                Phase(
                    id=model.id,
                    project_id=model.project_id,
                    name=model.name,
                    description=model.description,
                    status=PhaseStatus(model.status),
                    position=model.position,
                    start_date=model.start_date,
                    end_date=model.end_date,
                    section_id=model.section_id,
                    parallel_group=model.parallel_group,
                    created_at=model.created_at,
                    updated_at=model.updated_at,
                )
                for model in session.scalars(statement)
            ]
