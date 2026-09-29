from types import MethodType, SimpleNamespace

from kivy.uix.textinput import TextInput
from project_planner_frontend.projects.views.ProjectBrowser import ProjectBrowser
from project_planner_frontend.projects.views.ProjectCategoryRow import ProjectCategoryRow
from project_planner_frontend.projects.views.ProjectTreeRow import ProjectTreeRow
from project_planner_frontend.shared.ReorderableRow import ReorderableRow
from project_planner_frontend.shared.theme import style_input
from project_planner_frontend.shell.ProjectPlannerRoot import ProjectPlannerRoot

from project_planner.api.projects.dtos.ProjectTreeItem import ProjectTreeItem
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


def test_project_search_keeps_matching_project_ancestors() -> None:
    root = Project("Root")
    child = Project("Child", parent_id=root.id)
    target = Project("Target", parent_id=child.id)
    unrelated = Project("Unrelated")
    items = tuple(
        ProjectTreeItem(project, depth)
        for project, depth in ((root, 0), (child, 1), (target, 2), (unrelated, 0))
    )
    browser = SimpleNamespace(
        _parent_by_project_id={
            root.id: None,
            child.id: root.id,
            target.id: child.id,
            unrelated.id: None,
        }
    )

    filtered = ProjectBrowser._search_project_items(browser, items, "target", False)

    assert [item.project for item in filtered] == [root, child, target]
    assert ProjectBrowser._search_project_items(browser, items, "category", True) == items


def test_directory_rows_keep_actions_on_the_relevant_item() -> None:
    actions: list[str] = []
    category = ProjectCategoryRow(
        "category-1",
        "Client work",
        1,
        False,
        True,
        lambda: actions.append("select-category"),
        lambda: actions.append("toggle-category"),
        lambda: actions.append("add-project"),
        lambda: actions.append("rename-category"),
        lambda: actions.append("delete-category"),
    )
    project = ProjectTreeRow(
        "project-1",
        "Website",
        "active",
        1,
        False,
        True,
        True,
        lambda: actions.append("select-project"),
        lambda _position: None,
        lambda _position: actions.append("drop-project"),
        lambda: actions.append("toggle-project"),
        lambda: actions.append("add-child"),
        lambda: actions.append("archive-project"),
        lambda: actions.append("delete-project"),
    )

    assert category.add_project_button.text == "+"
    assert category.disclosure_button is not None
    assert category.gear_button is not None
    assert set(category.gear_button.action_buttons) == {"Rename"}
    assert category.delete_button is not None
    assert category.delete_button.__class__.__name__ == "BinButton"
    assert set(project.gear_button.action_buttons) == {"Add child", "Archive"}
    assert project.disclosure_button is not None
    assert project._indent_width > 0
    project.size = (500, 54)
    project.do_layout()
    assert project.button.markup is True
    assert project.button.text.index("Active") < project.button.text.index("Website")
    assert project.delete_button.__class__.__name__ == "BinButton"
    assert category.add_project_button.width == category.gear_button.width
    assert category.gear_button.width == category.delete_button.width
    category.disclosure_button.dispatch("on_release")
    category.add_project_button.dispatch("on_release")
    category.gear_button.action_buttons["Rename"].dispatch("on_release")
    category.delete_button.dispatch("on_release")
    project.disclosure_button.dispatch("on_release")
    project.gear_button.action_buttons["Add child"].dispatch("on_release")
    project.gear_button.action_buttons["Archive"].dispatch("on_release")
    project.delete_button.dispatch("on_release")

    assert actions == [
        "toggle-category",
        "add-project",
        "rename-category",
        "delete-category",
        "toggle-project",
        "add-child",
        "archive-project",
        "delete-project",
    ]


def test_archived_project_row_disables_its_archive_menu_action() -> None:
    project = ProjectTreeRow(
        "project-1",
        "Completed website",
        "archived",
        1,
        False,
        False,
        True,
        lambda: None,
        lambda _position: None,
        lambda _position: None,
        lambda: None,
        lambda: None,
        lambda: None,
        lambda: None,
    )

    archive_action = project.gear_button.action_buttons["Archived"]

    assert archive_action.disabled


def test_project_row_drag_dispatches_drop_instead_of_selection() -> None:
    actions: list[object] = []
    drag_events: list[object] = []
    project = ProjectTreeRow(
        "project-1",
        "Website",
        "active",
        1,
        False,
        False,
        True,
        lambda: actions.append("select"),
        lambda position: drag_events.append(position),
        lambda position: actions.append(position),
        lambda: None,
        lambda: None,
        lambda: None,
        lambda: None,
    )
    project.size = (500, 54)
    project.do_layout()
    touch = SimpleNamespace(
        pos=project.button.center,
        x=project.button.center_x,
        y=project.button.center_y,
        button="left",
        grab_current=None,
    )
    touch.grab = lambda widget: setattr(touch, "grab_current", widget)
    touch.ungrab = lambda _widget: setattr(touch, "grab_current", None)

    assert project.on_touch_down(touch)
    touch.x += 20
    touch.pos = (touch.x, touch.y)
    assert project.on_touch_move(touch)
    assert project.on_touch_up(touch)

    assert actions == [touch.pos]
    assert drag_events == [touch.pos, None]
    assert project.opacity == 1


def test_reorderable_row_dispatches_drop_instead_of_activation() -> None:
    events: list[object] = []
    row = ReorderableRow(
        "phase-1",
        lambda: events.append("activate"),
        lambda item_id, position: events.append(("drag", item_id, position)),
        lambda item_id, position: events.append(("drop", item_id, position)),
        size_hint_y=None,
        height=54,
    )
    primary = TextInput(text="Phase")
    row.add_widget(primary)
    row.set_primary_control(primary)
    row.size = (500, 54)
    row.do_layout()
    touch = SimpleNamespace(
        pos=primary.center,
        x=primary.center_x,
        y=primary.center_y,
        button="left",
        grab_current=None,
    )
    touch.grab = lambda widget: setattr(touch, "grab_current", widget)
    touch.ungrab = lambda _widget: setattr(touch, "grab_current", None)

    assert row.on_touch_down(touch)
    touch.x += 20
    touch.pos = (touch.x, touch.y)
    assert row.on_touch_move(touch)
    assert row.on_touch_up(touch)

    assert events == [
        ("drag", "phase-1", touch.pos),
        ("drag", "phase-1", None),
        ("drop", "phase-1", touch.pos),
    ]
    assert row.opacity == 1


def test_project_drop_resolves_category_and_parent_targets() -> None:
    moves: list[tuple[str, str | None, str | None]] = []
    reorders: list[tuple[str, str, bool]] = []
    category = ProjectCategoryRow(
        "category-1",
        "Client work",
        1,
        False,
        True,
        lambda: None,
        lambda: None,
        lambda: None,
        lambda: None,
        lambda: None,
    )
    target = ProjectTreeRow(
        "target-project",
        "Target",
        "active",
        1,
        False,
        False,
        True,
        lambda: None,
        lambda _position: None,
        lambda _position: None,
        lambda: None,
        lambda: None,
        lambda: None,
        lambda: None,
    )
    category.pos = (0, 60)
    category.size = (500, 40)
    target.pos = (0, 0)
    target.size = (500, 54)
    scroll = SimpleNamespace(
        x=0,
        y=0,
        width=500,
        height=100,
        top=100,
        scroll_y=1.0,
        collide_point=lambda x, y: 0 <= x <= 500 and 0 <= y <= 100,
    )
    browser = SimpleNamespace(
        _list=SimpleNamespace(
            children=[category, target],
            height=100,
            to_widget=lambda x, y: (x, y),
        ),
        _scroll=scroll,
        _category_by_project_id={target.project_id: "category-1"},
        _parent_by_project_id={target.project_id: None},
        _drop_target_widget=None,
        _drop_target_placement=None,
        _move_project=lambda project_id, parent_id, category_id: moves.append(
            (project_id, parent_id, category_id)
        ),
        _reorder_project=lambda project_id, target_id, after: reorders.append(
            (project_id, target_id, after)
        ),
    )
    browser._drop_target_at = MethodType(ProjectBrowser._drop_target_at, browser)
    browser._drag_project = MethodType(ProjectBrowser._drag_project, browser)
    browser._would_create_cycle = MethodType(ProjectBrowser._would_create_cycle, browser)
    browser._auto_scroll = MethodType(ProjectBrowser._auto_scroll, browser)

    ProjectBrowser._drag_project(browser, "source-project", category.center)
    assert category._drop_target_color.a == 1
    ProjectBrowser._drag_project(browser, "source-project", target.center)
    assert category._drop_target_color.a == 0
    assert target._drop_target_color.a == 1
    assert target._child_drop_target_color.a > 0

    ProjectBrowser._drag_project(browser, "source-project", (target.center_x, target.top - 1))
    assert target._drop_target_color.a == 0
    assert target._insert_target_color.a == 1
    assert target._insert_target_line.points[1] == target.top

    browser._parent_by_project_id[target.project_id] = "source-project"
    assert ProjectBrowser._drop_target_at(browser, "source-project", target.center) is None
    browser._parent_by_project_id[target.project_id] = None

    ProjectBrowser._drop_project(browser, "source-project", category.center)
    ProjectBrowser._drop_project(browser, "source-project", target.center)

    assert target._drop_target_color.a == 0
    assert moves == [
        ("source-project", None, "category-1"),
        ("source-project", "target-project", "category-1"),
    ]
    ProjectBrowser._drop_project(browser, "source-project", (target.center_x, target.top - 1))
    ProjectBrowser._drop_project(browser, "source-project", (target.center_x, target.y + 1))
    assert reorders == [
        ("source-project", "target-project", False),
        ("source-project", "target-project", True),
    ]


def test_collapsed_project_hides_only_its_descendants() -> None:
    root = Project("Root")
    child = Project("Child", parent_id=root.id)
    grandchild = Project("Grandchild", parent_id=child.id)
    sibling = Project("Sibling")
    items = (
        ProjectTreeItem(root, 0),
        ProjectTreeItem(child, 1),
        ProjectTreeItem(grandchild, 2),
        ProjectTreeItem(sibling, 0),
    )
    browser = SimpleNamespace(_collapsed_project_ids={root.id})

    visible = ProjectBrowser._visible_project_items(browser, items)

    assert [(item.project.title, has_children) for item, has_children in visible] == [
        ("Root", True),
        ("Sibling", False),
    ]


def test_directory_disclosure_toggles_rebuild_without_reloading() -> None:
    refreshes: list[bool] = []
    browser = SimpleNamespace(
        _collapsed_category_ids=set(),
        _collapsed_project_ids=set(),
        refresh=lambda *, reload=True: refreshes.append(reload),
    )

    ProjectBrowser._toggle_category(browser, "category-1")
    ProjectBrowser._toggle_project(browser, "project-1")
    ProjectBrowser._toggle_category(browser, "category-1")

    assert browser._collapsed_category_ids == set()
    assert browser._collapsed_project_ids == {"project-1"}
    assert refreshes == [False, False, False]


def test_browser_selection_uses_cached_directory_metadata() -> None:
    refreshes: list[bool] = []
    selections: list[tuple[str | None, bool]] = []
    browser = SimpleNamespace(
        selected_id=None,
        selected_category_id=None,
        _category_by_project_id={"project-1": "category-1"},
        _parent_by_project_id={"project-1": "parent-1", "parent-1": None},
        _collapsed_category_ids={"category-1"},
        _collapsed_project_ids={"parent-1"},
        refresh=lambda *, reload=True: refreshes.append(reload),
        _on_select=lambda project_id, refresh: selections.append((project_id, refresh)),
    )

    ProjectBrowser.select(browser, "project-1")

    assert browser.selected_category_id == "category-1"
    assert browser._collapsed_category_ids == set()
    assert browser._collapsed_project_ids == set()
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
