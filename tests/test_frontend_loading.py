from types import MethodType, SimpleNamespace

from project_planner_frontend.projects.views.ProjectBrowser import ProjectBrowser
from project_planner_frontend.shell.ProjectPlannerRoot import ProjectPlannerRoot

from project_planner.api.projects.queries.ProjectQueryService import ProjectQueryService
from project_planner.modules.projects.entities.Project import Project
from project_planner.modules.projects.entities.ProjectCategory import ProjectCategory


class CountingProjectService:
    def __init__(self, projects: tuple[Project, ...]) -> None:
        self._projects = projects
        self.list_calls = 0

    def list_all(self) -> tuple[Project, ...]:
        self.list_calls += 1
        return self._projects

    def require(self, _project_id: str) -> Project:
        raise AssertionError("Overview should use its existing project list")


class EmptyCategoryService:
    def __init__(self, categories: tuple[ProjectCategory, ...] = ()) -> None:
        self._categories = categories

    def list_all(self) -> tuple[object, ...]:
        return self._categories


def test_project_overview_uses_one_project_read() -> None:
    project = Project("Overview")
    projects = CountingProjectService((project,))
    queries = ProjectQueryService(projects, EmptyCategoryService())  # type: ignore[arg-type]

    overview = queries.get_overview(project.id)

    assert overview.project == project
    assert projects.list_calls == 1


def test_project_directory_groups_all_categories_from_one_project_read() -> None:
    category = ProjectCategory("Active", 0)
    categorized = Project("Categorized", category_id=category.id)
    uncategorized = Project("Uncategorized")
    projects = CountingProjectService((categorized, uncategorized))
    queries = ProjectQueryService(  # type: ignore[arg-type]
        projects,
        EmptyCategoryService((category,)),
    )

    directory = queries.list_directory()

    assert projects.list_calls == 1
    assert [section.category for section in directory] == [category, None]
    assert [item.project for section in directory for item in section.projects] == [
        categorized,
        uncategorized,
    ]


def test_browser_selection_uses_cached_directory_metadata() -> None:
    refreshes: list[bool] = []
    selections: list[str] = []
    browser = SimpleNamespace(
        selected_id=None,
        selected_category_id=None,
        _category_by_project_id={"project-1": "category-1"},
        refresh=lambda *, reload=True: refreshes.append(reload),
        _on_select=selections.append,
    )

    ProjectBrowser.select(browser, "project-1")

    assert browser.selected_category_id == "category-1"
    assert refreshes == [False]
    assert selections == ["project-1"]


def test_project_switch_loads_only_the_active_tab() -> None:
    loads: list[tuple[str, str]] = []
    current_tab = SimpleNamespace(text="Overview")
    root = SimpleNamespace(
        _selected_project_id=None,
        _loaded_project_by_tab={},
        _project_loaders={
            title: (lambda project_id, title=title: loads.append((title, project_id)))
            for title in ("Overview", "Plan Roadmap", "Diagram", "Workspace", "Links")
        },
        tabs=SimpleNamespace(current_tab=current_tab),
    )
    root._load_tab = MethodType(ProjectPlannerRoot._load_tab, root)

    ProjectPlannerRoot._show_project(root, "project-1")
    ProjectPlannerRoot._show_project(root, "project-1")
    current_tab.text = "Diagram"
    root._load_tab("Diagram")
    ProjectPlannerRoot._show_project(root, "project-2")

    assert loads == [
        ("Overview", "project-1"),
        ("Diagram", "project-1"),
        ("Diagram", "project-2"),
    ]
