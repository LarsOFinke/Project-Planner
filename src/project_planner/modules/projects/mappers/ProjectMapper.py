from project_planner.modules.projects.entities.PlanningMethod import PlanningMethod
from project_planner.modules.projects.entities.Project import Project
from project_planner.modules.projects.entities.ProjectStatus import ProjectStatus
from project_planner.shared.database.models.ProjectModel import ProjectModel


class ProjectMapper:
    @staticmethod
    def to_model(project: Project) -> ProjectModel:
        return ProjectModel(
            id=project.id,
            title=project.title,
            description=project.description,
            status=project.status.value,
            planning_method=project.planning_method.value,
            parent_id=project.parent_id,
            category_id=project.category_id,
            start_date=project.start_date,
            target_date=project.target_date,
            owner=project.owner,
            assignee=project.assignee,
            notes=project.notes,
            created_at=project.created_at,
            updated_at=project.updated_at,
        )

    @staticmethod
    def to_entity(model: ProjectModel) -> Project:
        return Project(
            id=model.id,
            title=model.title,
            description=model.description,
            status=ProjectStatus(model.status),
            planning_method=PlanningMethod(model.planning_method),
            parent_id=model.parent_id,
            category_id=model.category_id,
            start_date=model.start_date,
            target_date=model.target_date,
            owner=model.owner,
            assignee=model.assignee,
            notes=model.notes,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
