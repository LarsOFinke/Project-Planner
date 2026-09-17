from collections.abc import Sequence

from sqlalchemy import delete, select

from project_planner.core.domain.custom.PlanningSection import PlanningSection
from project_planner.core.domain.custom.SectionItem import SectionItem
from project_planner.core.domain.custom.SectionStatus import SectionStatus
from project_planner.core.domain.custom.SectionType import SectionType
from project_planner.core.infrastructure.database.Database import Database
from project_planner.core.infrastructure.database.models.PlanningSectionModel import (
    PlanningSectionModel,
)
from project_planner.core.infrastructure.database.models.SectionItemModel import SectionItemModel


class SQLAlchemySectionRepository:
    def __init__(self, database: Database) -> None:
        self._database = database

    def save(self, section: PlanningSection) -> None:
        with self._database.session() as session:
            session.merge(PlanningSectionModel(**self._section_values(section)))

    def save_all(self, project_id: str, sections: Sequence[PlanningSection]) -> None:
        with self._database.session() as session:
            existing = session.scalars(
                select(PlanningSectionModel).where(PlanningSectionModel.project_id == project_id)
            )
            for temporary_position, model in enumerate(existing, start=1):
                model.position = -temporary_position
            session.flush()
            for section in sections:
                session.merge(PlanningSectionModel(**self._section_values(section)))

    def get(self, section_id: str) -> PlanningSection | None:
        with self._database.session() as session:
            model = session.get(PlanningSectionModel, section_id)
            return self._section_domain(model) if model else None

    def list_for_project(self, project_id: str) -> Sequence[PlanningSection]:
        statement = (
            select(PlanningSectionModel)
            .where(PlanningSectionModel.project_id == project_id)
            .order_by(PlanningSectionModel.position)
        )
        with self._database.session() as session:
            return [self._section_domain(model) for model in session.scalars(statement)]

    def delete(self, section_id: str) -> None:
        with self._database.session() as session:
            session.execute(
                delete(PlanningSectionModel).where(PlanningSectionModel.id == section_id)
            )

    def save_item(self, item: SectionItem) -> None:
        with self._database.session() as session:
            session.merge(
                SectionItemModel(
                    id=item.id,
                    section_id=item.section_id,
                    title=item.title,
                    description=item.description,
                    assignee=item.assignee,
                    status=item.status.value,
                    item_date=item.item_date,
                    position=item.position,
                    created_at=item.created_at,
                    updated_at=item.updated_at,
                )
            )

    def save_items(self, section_id: str, items: Sequence[SectionItem]) -> None:
        with self._database.session() as session:
            existing = session.scalars(
                select(SectionItemModel).where(SectionItemModel.section_id == section_id)
            )
            for temporary_position, model in enumerate(existing, start=1):
                model.position = -temporary_position
            session.flush()
            for item in items:
                session.merge(
                    SectionItemModel(
                        id=item.id,
                        section_id=item.section_id,
                        title=item.title,
                        description=item.description,
                        assignee=item.assignee,
                        status=item.status.value,
                        item_date=item.item_date,
                        position=item.position,
                        created_at=item.created_at,
                        updated_at=item.updated_at,
                    )
                )

    def list_items(self, section_id: str) -> Sequence[SectionItem]:
        statement = (
            select(SectionItemModel)
            .where(SectionItemModel.section_id == section_id)
            .order_by(SectionItemModel.position)
        )
        with self._database.session() as session:
            return [
                SectionItem(
                    id=model.id,
                    section_id=model.section_id,
                    title=model.title,
                    description=model.description,
                    assignee=model.assignee,
                    status=SectionStatus(model.status),
                    item_date=model.item_date,
                    position=model.position,
                    created_at=model.created_at,
                    updated_at=model.updated_at,
                )
                for model in session.scalars(statement)
            ]

    def get_item(self, item_id: str) -> SectionItem | None:
        with self._database.session() as session:
            model = session.get(SectionItemModel, item_id)
            if model is None:
                return None
            return SectionItem(
                id=model.id,
                section_id=model.section_id,
                title=model.title,
                description=model.description,
                assignee=model.assignee,
                status=SectionStatus(model.status),
                item_date=model.item_date,
                position=model.position,
                created_at=model.created_at,
                updated_at=model.updated_at,
            )

    def delete_item(self, item_id: str) -> None:
        with self._database.session() as session:
            session.execute(delete(SectionItemModel).where(SectionItemModel.id == item_id))

    @staticmethod
    def _section_values(section: PlanningSection) -> dict[str, object]:
        return {
            "id": section.id,
            "project_id": section.project_id,
            "name": section.name,
            "description": section.description,
            "section_type": section.section_type.value,
            "position": section.position,
            "start_date": section.start_date,
            "end_date": section.end_date,
            "status": section.status.value,
            "created_at": section.created_at,
            "updated_at": section.updated_at,
        }

    @staticmethod
    def _section_domain(model: PlanningSectionModel) -> PlanningSection:
        return PlanningSection(
            id=model.id,
            project_id=model.project_id,
            name=model.name,
            description=model.description,
            section_type=SectionType(model.section_type),
            position=model.position,
            start_date=model.start_date,
            end_date=model.end_date,
            status=SectionStatus(model.status),
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
