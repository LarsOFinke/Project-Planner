import sqlite3

from project_planner.core.domain.shared.clock import utc_now

SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL CHECK (length(trim(title)) > 0),
    description TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL,
    planning_method TEXT NOT NULL,
    parent_id TEXT REFERENCES projects(id) ON DELETE SET NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_projects_parent ON projects(parent_id);
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);

CREATE TABLE IF NOT EXISTS phases (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'planned',
    position INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(project_id, position)
);

CREATE TABLE IF NOT EXISTS project_links (
    source_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    target_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    relation TEXT NOT NULL DEFAULT 'related',
    note TEXT NOT NULL DEFAULT '',
    PRIMARY KEY(source_id, target_id, relation),
    CHECK(source_id <> target_id)
);

CREATE TABLE IF NOT EXISTS artifacts (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    kind TEXT NOT NULL CHECK(kind IN ('diagram', 'workspace')),
    content TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_artifacts_project_kind
ON artifacts(project_id, kind);
"""


def migrate_schema(connection: sqlite3.Connection) -> None:
    phase_columns = {
        row["name"] for row in connection.execute("PRAGMA table_info(phases)").fetchall()
    }
    additions = {
        "status": "TEXT NOT NULL DEFAULT 'planned'",
        "created_at": "TEXT NOT NULL DEFAULT ''",
        "updated_at": "TEXT NOT NULL DEFAULT ''",
    }
    for name, declaration in additions.items():
        if name not in phase_columns:
            connection.execute(f"ALTER TABLE phases ADD COLUMN {name} {declaration}")
    timestamp = utc_now().isoformat()
    connection.execute(
        "UPDATE phases SET created_at = ? WHERE created_at = ''", (timestamp,)
    )
    connection.execute(
        "UPDATE phases SET updated_at = created_at WHERE updated_at = ''"
    )
