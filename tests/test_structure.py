import ast
from pathlib import Path

SOURCE_PACKAGES = (
    (Path("src/project_planner"), Path("src")),
    (Path("frontend/src/project_planner_frontend"), Path("frontend/src")),
)


def _source_paths() -> list[Path]:
    return [path for package, _root in SOURCE_PACKAGES for path in package.rglob("*.py")]


def _imported_modules(path: Path) -> list[str]:
    modules: list[str] = []
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            modules.append(node.module)
    return modules


def _direct_source_import_graph() -> dict[str, set[str]]:
    modules: dict[str, Path] = {}
    for package, source_root in SOURCE_PACKAGES:
        for path in package.rglob("*.py"):
            if path.name != "__init__.py":
                module = ".".join(path.relative_to(source_root).with_suffix("").parts)
                modules[module] = path
    return {
        module: {imported for imported in _imported_modules(path) if imported in modules}
        for module, path in modules.items()
    }


def test_every_source_file_contains_at_most_one_class() -> None:
    violations: list[str] = []
    for path in _source_paths():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        if len(classes) > 1:
            violations.append(f"{path}: {', '.join(classes)}")

    assert not violations, "More than one class in: " + "; ".join(violations)


def test_class_module_filename_matches_class_name() -> None:
    violations: list[str] = []
    for path in _source_paths():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        if len(classes) == 1 and path.stem != classes[0]:
            violations.append(f"{path}: expected {classes[0]}.py")

    assert not violations, "Class module filename mismatch: " + "; ".join(violations)


def test_direct_source_modules_do_not_form_import_cycles() -> None:
    graph = _direct_source_import_graph()
    visiting: list[str] = []
    visited: set[str] = set()
    cycles: list[str] = []

    def visit(module: str) -> None:
        if module in visiting:
            start = visiting.index(module)
            cycles.append(" -> ".join([*visiting[start:], module]))
            return
        if module in visited:
            return
        visiting.append(module)
        for dependency in graph[module]:
            visit(dependency)
        visiting.pop()
        visited.add(module)

    for module in graph:
        visit(module)

    assert not cycles, "Direct source import cycles: " + "; ".join(cycles)


def test_frontend_does_not_overwrite_kivy_parent_property() -> None:
    frontend_root = Path("frontend/src/project_planner_frontend")
    violations: list[str] = []
    for path in frontend_root.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            targets: list[ast.expr] = []
            if isinstance(node, ast.Assign):
                targets = node.targets
            elif isinstance(node, ast.AnnAssign):
                targets = [node.target]
            for target in targets:
                if (
                    isinstance(target, ast.Attribute)
                    and isinstance(target.value, ast.Name)
                    and target.value.id == "self"
                    and target.attr == "parent"
                ):
                    violations.append(f"{path}:{node.lineno}")

    assert not violations, "Kivy's reserved self.parent was overwritten: " + ", ".join(violations)


def test_backend_remains_independent_from_frontend_and_kivy() -> None:
    violations: list[str] = []
    for path in Path("src/project_planner").rglob("*.py"):
        for module in _imported_modules(path):
            if module == "kivy" or module.startswith(("kivy.", "project_planner_frontend")):
                violations.append(f"{path}: {module}")

    assert not violations, "Backend dependency boundary violations: " + "; ".join(violations)


def test_feature_module_layers_depend_inward() -> None:
    violations: list[str] = []
    forbidden_entities = (
        ".repositories",
        ".gateways",
        ".mappers",
        ".dtos",
        ".protocols",
        ".services",
    )
    for path in Path("src/project_planner/modules").glob("*/entities/**/*.py"):
        for module in _imported_modules(path):
            if any(part in module for part in forbidden_entities) or module.startswith(
                "project_planner.api"
            ):
                violations.append(f"{path}: {module}")
    for path in Path("src/project_planner/modules").glob("*/dtos/**/*.py"):
        for module in _imported_modules(path):
            if (
                ".repositories" in module
                or ".gateways" in module
                or ".mappers" in module
                or ".services" in module
            ):
                violations.append(f"{path}: {module}")
    for path in Path("src/project_planner/modules").glob("*/protocols/**/*.py"):
        for module in _imported_modules(path):
            if (
                ".repositories" in module
                or ".gateways" in module
                or ".mappers" in module
                or ".services" in module
                or module.startswith("project_planner.api")
            ):
                violations.append(f"{path}: {module}")
    for path in Path("src/project_planner/modules").glob("*/services/**/*.py"):
        for module in _imported_modules(path):
            if (
                ".repositories" in module
                or ".gateways" in module
                or ".mappers" in module
                or module.startswith("project_planner.shared.database")
            ):
                violations.append(f"{path}: {module}")

    assert not violations, "Inward dependency violations: " + "; ".join(violations)


def test_frontend_uses_clients_instead_of_persistence_repositories() -> None:
    violations: list[str] = []
    for path in Path("frontend/src/project_planner_frontend").rglob("*.py"):
        for module in _imported_modules(path):
            if (
                module == "sqlite3"
                or module.startswith(("sqlalchemy", "project_planner.shared.database"))
                or ".repositories" in module
                or ".gateways" in module
            ):
                violations.append(f"{path}: {module}")

    assert not violations, "Frontend persistence boundary violations: " + "; ".join(violations)


def test_feature_modules_do_not_reintroduce_adapter_directories() -> None:
    adapters = list(Path("src/project_planner/modules").glob("*/adapters"))
    assert not adapters, f"Use repositories/ for persistence implementations: {adapters}"


def test_feature_controllers_own_their_http_routes() -> None:
    router_directory = Path("src/project_planner/api/http/routers")
    assert not router_directory.exists(), "Routes belong directly to feature controllers"

    violations: list[str] = []
    controllers = list(Path("src/project_planner/api").glob("*/[A-Z]*Controller.py"))
    for path in controllers:
        source = path.read_text(encoding="utf-8")
        if "APIRouter" not in source or "self.router" not in source:
            violations.append(str(path))

    assert len(controllers) == 5, f"Expected five feature controllers, found: {controllers}"
    assert not violations, "Controllers without owned HTTP routes: " + "; ".join(violations)


def test_controller_route_registration_is_grouped_by_resource() -> None:
    violations: list[str] = []
    for path in Path("src/project_planner/api").glob("*/[A-Z]*Controller.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        register_routes = next(
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef) and node.name == "_register_routes"
        )
        delegated_helpers = {
            node.func.attr
            for node in ast.walk(register_routes)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr.startswith("_register_")
            and node.func.attr.endswith("_routes")
        }
        directly_registers_routes = any(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "add_api_route"
            for node in ast.walk(register_routes)
        )
        if len(delegated_helpers) < 2 or directly_registers_routes:
            violations.append(str(path))

    assert not violations, "Split route registration into resource helpers: " + "; ".join(
        violations
    )


def test_api_is_split_into_feature_modules_with_dtos() -> None:
    api_root = Path("src/project_planner/api")
    expected_features = {
        "projects": "ProjectController.py",
        "planning": "PlanningController.py",
        "collaboration": "CollaborationController.py",
        "artifacts": "ArtifactController.py",
        "system": "SystemController.py",
    }
    missing = [
        feature
        for feature, controller in expected_features.items()
        if not (api_root / feature / controller).is_file()
        or not (api_root / feature / "dtos").is_dir()
    ]
    module_dto_directories = list(Path("src/project_planner/modules").glob("*/dtos"))

    assert not missing, f"Incomplete API feature modules: {missing}"
    assert not module_dto_directories, (
        f"Transport DTOs belong to API feature modules: {module_dto_directories}"
    )


def test_api_has_no_aggregate_container_module() -> None:
    containers = list(Path("src/project_planner/api").rglob("*Container.py"))
    assert not containers, (
        f"Use feature controllers instead of an aggregate container: {containers}"
    )


def test_planning_strategies_share_one_backend_module() -> None:
    modules_root = Path("src/project_planner/modules")
    legacy_modules = ("agile", "custom", "phases", "waterfall")
    legacy_sources = [
        path for module in legacy_modules for path in (modules_root / module).rglob("*.py")
    ]

    assert not legacy_sources, f"Planning code belongs in modules/planning: {legacy_sources}"
    assert (modules_root / "planning/entities").is_dir()
    assert (modules_root / "planning/services").is_dir()


def test_frontend_mirrors_api_feature_boundaries() -> None:
    frontend_root = Path("frontend/src/project_planner_frontend")
    expected_features = {"projects", "planning", "collaboration", "artifacts", "system"}
    missing = [feature for feature in expected_features if not (frontend_root / feature).is_dir()]
    legacy_clients = list((frontend_root / "clients").glob("*.py"))

    assert not missing, f"Missing frontend API feature boundaries: {missing}"
    assert not legacy_clients, f"Move feature clients beside their views: {legacy_clients}"


def test_frontend_does_not_import_backend_service_or_composition_types() -> None:
    violations: list[str] = []
    allowed_pure_services = (
        "project_planner.modules.calendar.services",
        "project_planner.modules.artifacts.services.codecs",
    )
    for path in Path("frontend/src/project_planner_frontend").rglob("*.py"):
        for module in _imported_modules(path):
            embedded_server_bootstrap = (
                path.name == "ProjectPlannerApp.py"
                and module == "project_planner.api.http.ApiServer"
            )
            api_contract = "/clients/" in path.as_posix() and ".dtos" in module
            if (
                module.startswith("project_planner.api")
                and not embedded_server_bootstrap
                and not api_contract
            ) or (".services" in module and not module.startswith(allowed_pure_services)):
                violations.append(f"{path}: {module}")

    assert not violations, "Frontend backend-coupling violations: " + "; ".join(violations)
