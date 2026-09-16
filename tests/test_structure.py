import ast
from pathlib import Path


def test_every_source_file_contains_at_most_one_class() -> None:
    source_root = Path("src/project_planner")
    violations: list[str] = []
    for path in source_root.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        if len(classes) > 1:
            violations.append(f"{path}: {', '.join(classes)}")

    assert not violations, "More than one class in: " + "; ".join(violations)


def test_frontend_does_not_overwrite_kivy_parent_property() -> None:
    frontend_root = Path("src/project_planner/frontend")
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

    assert not violations, "Kivy's reserved self.parent was overwritten: " + ", ".join(
        violations
    )
