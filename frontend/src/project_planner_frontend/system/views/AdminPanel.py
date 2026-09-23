from collections.abc import Callable
from datetime import date
from functools import partial

from kivy import __version__ as kivy_version
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView

from project_planner.modules.health.entities.ApplicationIssue import ApplicationIssue
from project_planner_frontend.shared.background import run_background
from project_planner_frontend.shared.dialogs import (
    open_confirmation_dialog,
    open_details_dialog,
    open_file_dialog,
    open_save_file_dialog,
    show_confirmation,
    show_error,
)
from project_planner_frontend.shared.theme import (
    BORDER,
    NAVY_800,
    NAVY_900,
    PEARL_GREY,
    RED,
    SLATE_200,
    SLATE_400,
    caption_label,
    paint_background,
    section_label,
    style_button,
    title_label,
)
from project_planner_frontend.system.clients.DatabaseTransferClient import DatabaseTransferClient
from project_planner_frontend.system.clients.HealthClient import HealthClient
from project_planner_frontend.system.clients.IssueClient import IssueClient


class AdminPanel(BoxLayout):
    def __init__(
        self,
        health: HealthClient,
        issues: IssueClient,
        database_transfer: DatabaseTransferClient,
        on_database_imported: Callable[[], None],
        **kwargs: object,
    ) -> None:
        super().__init__(orientation="vertical", **kwargs)
        self._health = health
        self._issues = issues
        self._database_transfer = database_transfer
        self._on_database_imported = on_database_imported
        self._refresh_generation = 0
        paint_background(self, NAVY_900)
        content = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=dp(10),
            padding=[dp(22), dp(18)],
        )
        content.bind(minimum_height=content.setter("height"))
        heading = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        heading.add_widget(title_label("Admin and health"))
        refresh = style_button(Button(text="Refresh", size_hint_x=None, width=dp(120)), "secondary")
        refresh.bind(on_release=self.refresh)
        heading.add_widget(refresh)
        content.add_widget(heading)
        content.add_widget(
            caption_label("Runtime health, complete backups, and recorded application errors.")
        )
        self.health_summary = Label(
            text="",
            color=SLATE_200,
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=dp(132),
        )
        self.health_summary.bind(size=lambda widget, size: setattr(widget, "text_size", size))
        self.health_summary.padding = [dp(16), dp(10)]
        paint_background(self.health_summary, NAVY_800, 8, BORDER)
        content.add_widget(self.health_summary)
        content.add_widget(section_label("Complete backup"))
        content.add_widget(self._build_database_transfer())
        content.add_widget(section_label("Recent issues"))
        self._rows = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(6))
        self._rows.bind(minimum_height=self._rows.setter("height"))
        content.add_widget(self._rows)
        scroll = ScrollView(do_scroll_x=False, bar_width=dp(5))
        scroll.add_widget(content)
        self.add_widget(scroll)
        self.refresh()

    def _build_database_transfer(self) -> BoxLayout:
        surface = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=dp(126),
            spacing=dp(10),
            padding=[dp(16), dp(12)],
        )
        paint_background(surface, NAVY_800, 8, BORDER)
        surface.add_widget(
            caption_label(
                "Export a tarball containing the database and managed files. Dry run validates "
                "a backup before merging its records and restoring missing files."
            )
        )
        actions = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        self.export_button = style_button(Button(text="Export backup"), "primary")
        self.dry_run_button = style_button(Button(text="Dry run"), "secondary")
        self.import_button = style_button(Button(text="Import backup"), "secondary")
        self.export_button.bind(on_release=lambda *_: self._choose_export_destination())
        self.dry_run_button.bind(on_release=lambda *_: self._choose_dry_run_source())
        self.import_button.bind(on_release=lambda *_: self._choose_import_source())
        actions.add_widget(self.export_button)
        actions.add_widget(self.dry_run_button)
        actions.add_widget(self.import_button)
        surface.add_widget(actions)
        return surface

    def _choose_export_destination(self) -> None:
        open_save_file_dialog(
            "Export backup",
            f"project-planner-{date.today().isoformat()}.tar.gz",
            self._export_database,
        )

    def _export_database(self, destination: str) -> None:
        run_background(
            lambda: self._database_transfer.export_to(destination),
            lambda path: show_confirmation(f"Backup exported to\n{path}"),
            lambda error: show_error(f"Backup export failed:\n{error}"),
        )

    def _choose_import_source(self) -> None:
        open_file_dialog(
            self._confirm_import,
            title="Import backup",
            action_text="Review import",
            filters=("*.tar.gz", "*.TAR.GZ"),
        )

    def _choose_dry_run_source(self) -> None:
        open_file_dialog(
            self._dry_run_import,
            title="Dry-run backup import",
            action_text="Run validation",
            filters=("*.tar.gz", "*.TAR.GZ"),
        )

    def _dry_run_import(self, source: str) -> None:
        run_background(
            lambda: self._database_transfer.dry_run_import(source),
            self._show_dry_run_report,
            lambda error: show_error(f"Backup dry run failed:\n{error}"),
        )

    def _show_dry_run_report(self, report: object) -> None:
        open_details_dialog(
            "Backup dry run complete",
            (
                "Validation succeeded and no changes were saved.\n\n"
                f"Records to create: {report.created}\n"
                f"Records to update: {report.updated}\n"
                f"Records already identical: {report.unchanged}\n\n"
                f"Managed files to restore: {report.files_created}\n"
                f"Managed files already identical: {report.files_unchanged}"
            ),
        )

    def _confirm_import(self, source: str) -> None:
        open_confirmation_dialog(
            "Apply backup import",
            (
                "Merge this backup into the current database and restore its managed files? "
                "Existing records and files absent from the backup will remain. "
                "Conflicting local files will stop the import."
            ),
            partial(self._apply_import, source),
            confirm_text="Import",
            confirm_variant="primary",
        )

    def _apply_import(self, source: str) -> None:
        run_background(
            lambda: self._database_transfer.import_from(source),
            self._import_finished,
            lambda error: show_error(f"Backup import failed:\n{error}"),
        )

    def _import_finished(self, report: object) -> None:
        self._on_database_imported()
        self.refresh()
        show_confirmation(
            "Backup import complete:\n"
            f"Records: {report.created} created, {report.updated} updated, "
            f"{report.unchanged} unchanged.\n"
            f"Managed files: {report.files_created} restored, "
            f"{report.files_unchanged} already identical."
        )

    def refresh(self, *_: object) -> None:
        self._refresh_generation += 1
        generation = self._refresh_generation

        def fetch():
            health = self._health.snapshot()
            issues = self._issues.list_recent(50) if health.database_healthy else []
            return health, issues

        def display(result: tuple[object, list[ApplicationIssue]]) -> None:
            if generation != self._refresh_generation:
                return
            self._display_status(*result)

        run_background(fetch, display)

    def _display_status(self, health: object, issues: list[ApplicationIssue]) -> None:
        status = "Healthy" if health.database_healthy else "Unavailable"
        self.health_summary.text = (
            f"Project Planner {health.app_version}  ·  Kivy {kivy_version}  ·  "
            f"Python {health.python_version}\n"
            f"Database: {status} ({health.database_backend})\n"
            f"Location: {health.database_location}\n"
            f"Recorded issues: {health.issue_count}"
        )
        self.health_summary.color = PEARL_GREY if health.database_healthy else RED
        self.export_button.disabled = not health.database_healthy
        self.dry_run_button.disabled = not health.database_healthy
        self.import_button.disabled = not health.database_healthy
        self._rows.clear_widgets()
        if not issues:
            self._rows.add_widget(
                Label(
                    text="No application issues have been recorded.",
                    color=SLATE_400,
                    size_hint_y=None,
                    height=dp(64),
                )
            )
            return
        for issue in issues:
            self._add_issue(issue)

    def _add_issue(self, issue: ApplicationIssue) -> None:
        row = BoxLayout(size_hint_y=None, height=dp(72), spacing=dp(6))
        occurred = issue.occurred_at.astimezone().strftime("%Y-%m-%d %H:%M:%S")
        summary = Label(
            text=(f"{occurred}  ·  {issue.exception_type}\n{issue.source}  ·  {issue.message}"),
            color=SLATE_200,
            halign="left",
            valign="middle",
            shorten=True,
            shorten_from="right",
        )
        summary.bind(
            size=lambda widget, size: setattr(widget, "text_size", (size[0] - dp(8), size[1]))
        )
        details = style_button(Button(text="Details", size_hint_x=None, width=dp(100)), "secondary")
        details.bind(on_release=partial(self._show_details, issue))
        row.add_widget(summary)
        row.add_widget(details)
        self._rows.add_widget(row)

    @staticmethod
    def _show_details(issue: ApplicationIssue, *_: object) -> None:
        open_details_dialog(
            f"{issue.exception_type} · {issue.id}",
            (
                f"Occurred: {issue.occurred_at.astimezone().isoformat()}\n"
                f"Source: {issue.source}\n"
                f"Message: {issue.message}\n\n"
                f"{issue.traceback}"
            ),
        )
