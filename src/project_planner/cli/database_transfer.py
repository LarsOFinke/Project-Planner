import argparse
from collections.abc import Sequence

from project_planner.core.configuration.settings_loader import load_settings
from project_planner.core.infrastructure.database.Database import Database
from project_planner.core.infrastructure.transfer.DatabaseTransferService import (
    DatabaseTransferService,
)


def main(arguments: Sequence[str] | None = None) -> int:
    parser = _parser()
    options = parser.parse_args(arguments)
    settings = load_settings(options.config)
    database = Database(settings.database_path, settings.database_url)
    transfer = DatabaseTransferService(database)
    if options.command == "export":
        path = transfer.export_to(options.path)
        print(f"Exported database to {path}")
        return 0
    report = transfer.import_from(options.path, dry_run=not options.apply)
    mode = "Dry run" if report.dry_run else "Import"
    print(f"{mode} successful: {report.created} create, {report.updated} update")
    if report.dry_run:
        print("No changes were saved. Re-run with --apply to import.")
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Export or import Project Planner data")
    parser.add_argument("--config", help="Optional configuration file")
    commands = parser.add_subparsers(dest="command", required=True)
    export = commands.add_parser("export", help="Export all database records as JSON")
    export.add_argument("path")
    import_command = commands.add_parser(
        "import", help="Validate an export; dry-run is the default"
    )
    import_command.add_argument("path")
    mode = import_command.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true", help="Commit the imported records")
    mode.add_argument("--dry-run", action="store_true", help="Validate and roll back (the default)")
    return parser


if __name__ == "__main__":
    raise SystemExit(main())
