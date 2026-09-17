from collections.abc import Sequence
from datetime import date

from project_planner.core.application.phases.PhaseService import PhaseService
from project_planner.core.domain.custom.PlanningSection import PlanningSection
from project_planner.core.domain.custom.SectionItem import SectionItem
from project_planner.core.domain.custom.SectionStatus import SectionStatus
from project_planner.core.domain.custom.SectionType import SectionType
from project_planner.core.ports.SectionRepository import SectionRepository


class SectionService:
    def __init__(self, repository: SectionRepository, phases: PhaseService) -> None:
        self._repository = repository
        self._phases = phases

    def list_for_project(self, project_id: str) -> Sequence[PlanningSection]:
        return self._repository.list_for_project(project_id)

    def add(
        self,
        project_id: str,
        name: str,
        section_type: SectionType,
        description: str = "",
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> PlanningSection:
        section = PlanningSection(
            project_id=project_id,
            name=name.strip(),
            section_type=section_type,
            position=len(self.list_for_project(project_id)),
            description=description.strip(),
            start_date=start_date,
            end_date=end_date,
        )
        self._repository.save(section)
        self._add_template(section)
        return section

    def update(
        self,
        section_id: str,
        *,
        name: str,
        description: str,
        section_type: SectionType,
        start_date: date | None,
        end_date: date | None,
        status: SectionStatus,
    ) -> PlanningSection:
        section = self.require(section_id)
        updated = section.revise(
            name=name.strip(),
            description=description.strip(),
            section_type=section_type,
            start_date=start_date,
            end_date=end_date,
            status=status,
        )
        self._repository.save(updated)
        if section.section_type is not section_type:
            self._add_template(updated)
        return updated

    def require(self, section_id: str) -> PlanningSection:
        section = self._repository.get(section_id)
        if section is None:
            raise LookupError(f"Section {section_id!r} does not exist")
        return section

    def move(self, project_id: str, section_id: str, offset: int) -> None:
        sections = list(self.list_for_project(project_id))
        index = next(index for index, section in enumerate(sections) if section.id == section_id)
        target = max(0, min(len(sections) - 1, index + offset))
        if index == target:
            return
        sections[index], sections[target] = sections[target], sections[index]
        reordered = [section.revise(position=position) for position, section in enumerate(sections)]
        self._repository.save_all(project_id, reordered)

    def remove(self, section_id: str) -> None:
        section = self.require(section_id)
        self._repository.delete(section_id)
        remaining = list(self.list_for_project(section.project_id))
        normalized = [item.revise(position=position) for position, item in enumerate(remaining)]
        self._repository.save_all(section.project_id, normalized)

    def list_items(self, section_id: str) -> Sequence[SectionItem]:
        return self._repository.list_items(section_id)

    def add_item(
        self,
        section_id: str,
        title: str,
        description: str = "",
        assignee: str = "",
        status: SectionStatus = SectionStatus.NOT_STARTED,
        item_date: date | None = None,
    ) -> SectionItem:
        item = SectionItem(
            section_id=section_id,
            title=title.strip(),
            description=description.strip(),
            assignee=assignee.strip(),
            status=status,
            item_date=item_date,
            position=len(self.list_items(section_id)),
        )
        self._repository.save_item(item)
        return item

    def remove_item(self, item_id: str) -> None:
        item = self._repository.get_item(item_id)
        if item is None:
            raise LookupError(f"Section item {item_id!r} does not exist")
        self._repository.delete_item(item_id)
        remaining = list(self.list_items(item.section_id))
        normalized = [
            current.revise(position=position) for position, current in enumerate(remaining)
        ]
        self._repository.save_items(item.section_id, normalized)

    def update_item(
        self,
        item: SectionItem,
        *,
        title: str,
        description: str,
        assignee: str,
        status: SectionStatus,
        item_date: date | None,
    ) -> SectionItem:
        updated = item.revise(
            title=title.strip(),
            description=description.strip(),
            assignee=assignee.strip(),
            status=status,
            item_date=item_date,
        )
        self._repository.save_item(updated)
        return updated

    def move_item(self, section_id: str, item_id: str, offset: int) -> None:
        items = list(self.list_items(section_id))
        index = next(index for index, item in enumerate(items) if item.id == item_id)
        target = max(0, min(len(items) - 1, index + offset))
        if index == target:
            return
        items[index], items[target] = items[target], items[index]
        reordered = [item.revise(position=position) for position, item in enumerate(items)]
        self._repository.save_items(section_id, reordered)

    def _add_template(self, section: PlanningSection) -> None:
        if section.section_type is SectionType.WATERFALL:
            self._phases.initialize_waterfall(section.project_id, section.id)
