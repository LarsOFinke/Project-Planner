from collections.abc import Sequence

from project_planner.modules.projects.entities.ProjectCategory import ProjectCategory
from project_planner.modules.projects.protocols.ProjectCategoryRepository import (
    ProjectCategoryRepository,
)


class ProjectCategoryService:
    def __init__(self, categories: ProjectCategoryRepository) -> None:
        self._categories = categories

    def create(self, name: str) -> ProjectCategory:
        normalized = name.strip()
        if any(item.name.casefold() == normalized.casefold() for item in self.list_all()):
            raise ValueError(f"Project category {normalized!r} already exists")
        categories = self.list_all()
        position = max((item.position for item in categories), default=-1) + 1
        category = ProjectCategory(name=normalized, position=position)
        self._categories.save(category)
        return category

    def require(self, category_id: str) -> ProjectCategory:
        category = self._categories.get(category_id)
        if category is None:
            raise LookupError(f"Project category {category_id!r} does not exist")
        return category

    def rename(self, category_id: str, name: str) -> ProjectCategory:
        category = self.require(category_id)
        normalized = name.strip()
        if not normalized:
            raise ValueError("Project category name must not be empty")
        if any(
            item.id != category_id and item.name.casefold() == normalized.casefold()
            for item in self.list_all()
        ):
            raise ValueError(f"Project category {normalized!r} already exists")
        updated = category.revise(name=normalized)
        self._categories.save(updated)
        return updated

    def list_all(self) -> Sequence[ProjectCategory]:
        return self._categories.list_all()

    def delete(self, category_id: str) -> None:
        self.require(category_id)
        self._categories.delete(category_id)
