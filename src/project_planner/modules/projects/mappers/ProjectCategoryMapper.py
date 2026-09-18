from project_planner.modules.projects.entities.ProjectCategory import ProjectCategory
from project_planner.shared.database.models.ProjectCategoryModel import ProjectCategoryModel


class ProjectCategoryMapper:
    @staticmethod
    def to_model(category: ProjectCategory) -> ProjectCategoryModel:
        return ProjectCategoryModel(
            id=category.id,
            name=category.name,
            position=category.position,
            created_at=category.created_at,
            updated_at=category.updated_at,
        )

    @staticmethod
    def to_entity(model: ProjectCategoryModel) -> ProjectCategory:
        return ProjectCategory(
            id=model.id,
            name=model.name,
            position=model.position,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
