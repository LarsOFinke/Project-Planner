from types import MethodType, SimpleNamespace

from kivy.uix.textinput import TextInput
from project_planner_frontend.projects.views.ProjectBrowser import ProjectBrowser
from project_planner_frontend.projects.views.ProjectCategoryRow import ProjectCategoryRow
from project_planner_frontend.projects.views.ProjectTreeRow import ProjectTreeRow
from project_planner_frontend.shared.theme import style_input
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


def test_styled_input_background_precedes_kivy_text_and_cursor_instructions() -> None:
    field = style_input(TextInput(text="Visible project title"))

    assert field.canvas.before.children[0] is field._theme_input_background
    assert field.foreground_color != field._theme_input_color.rgba


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


def test_project_directory_always_exposes_uncategorized_creation_target() -> None:
    queries = ProjectQueryService(  # type: ignore[arg-type]
        CountingProjectService(()),
        EmptyCategoryService(),
    )

    directory = queries.list_directory()

    assert len(directory) == 1
    assert directory[0].category is None
    assert directory[0].projects == ()


def test_directory_rows_keep_actions_on_the_relevant_item() -> None:
    actions: list[str] = []
    category = ProjectCategoryRow(
        "Client work",
        1,
        False,
        lambda: actions.append("select-category"),
        lambda: actions.append("add-project"),
        lambda: actions.append("rename-category"),
        lambda: actions.append("delete-category"),
    )
    project = ProjectTreeRow(
        "Website",
        "active",
        1,
        False,
        lambda: actions.append("select-project"),
        lambda: actions.append("add-child"),
        lambda: actions.append("archive-project"),
        lambda: actions.append("delete-project"),
    )

    assert category.add_project_button.text == "+"
    assert category.gear_button is not None
    assert set(category.gear_button.action_buttons) == {"Rename"}
    assert category.delete_button is not None
    assert category.delete_button.__class__.__name__ == "BinButton"
    assert set(project.gear_button.action_buttons) == {"Add child", "Archive"}
    assert project.delete_button.__class__.__name__ == "BinButton"
    category.add_project_button.dispatch("on_release")
    category.gear_button.action_buttons["Rename"].dispatch("on_release")
    category.delete_button.dispatch("on_release")
    project.gear_button.action_buttons["Add child"].dispatch("on_release")
    project.gear_button.action_buttons["Archive"].dispatch("on_release")
    project.delete_button.dispatch("on_release")

    assert actions == [
        "add-project",
        "rename-category",
        "delete-category",
        "add-child",
        "archive-project",
        "delete-project",
    ]


def test_archived_project_row_disables_its_archive_menu_action() -> None:
    project = ProjectTreeRow(
        "Completed website",
        "archived",
        1,
        False,
        lambda: None,
        lambda: None,
        lambda: None,
        lambda: None,
    )

    archive_action = project.gear_button.action_buttons["Archived"]

    assert archive_action.disabled


def test_browser_selection_uses_cached_directory_metadata() -> None:
    refreshes: list[bool] = []
    selections: list[tuple[str | None, bool]] = []
    browser = SimpleNamespace(
        selected_id=None,
        selected_category_id=None,
        _category_by_project_id={"project-1": "category-1"},
        refresh=lambda *, reload=True: refreshes.append(reload),
        _on_select=lambda project_id, refresh: selections.append((project_id, refresh)),
    )

    ProjectBrowser.select(browser, "project-1")

    assert browser.selected_category_id == "category-1"
    assert refreshes == [False]
    assert selections == [("project-1", False)]


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


def test_clearing_project_resets_every_project_panel() -> None:
    cleared: list[str] = []
    root = SimpleNamespace(
        _selected_project_id="project-1",
        _loaded_project_by_tab={"Overview": "project-1"},
        overview=SimpleNamespace(clear_project=lambda: cleared.append("Overview")),
        planning=SimpleNamespace(clear_project=lambda: cleared.append("Plan Roadmap")),
        links=SimpleNamespace(clear_project=lambda: cleared.append("Links")),
        diagram=SimpleNamespace(clear_project=lambda: cleared.append("Diagram")),
        workspace=SimpleNamespace(clear_project=lambda: cleared.append("Workspace")),
    )

    ProjectPlannerRoot._show_project(root, None, True)

    assert root._selected_project_id is None
    assert root._loaded_project_by_tab == {}
    assert cleared == ["Overview", "Plan Roadmap", "Links", "Diagram", "Workspace"]
