from functools import partial

from kivy import __version__ as kivy_version
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView

from project_planner.core.application.health.IssueLogService import IssueLogService
from project_planner.core.application.health.SystemHealthService import SystemHealthService
from project_planner.core.domain.health.ApplicationIssue import ApplicationIssue
from project_planner.frontend.shared.dialogs import open_details_dialog
from project_planner.frontend.shared.theme import (
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


class AdminPanel(BoxLayout):
    def __init__(
        self,
        health: SystemHealthService,
        issues: IssueLogService,
        **kwargs: object,
    ) -> None:
        super().__init__(
            orientation="vertical",
            spacing=dp(10),
            padding=[dp(22), dp(18)],
            **kwargs,
        )
        self._health = health
        self._issues = issues
        paint_background(self, NAVY_900)
        heading = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        heading.add_widget(title_label("Admin and health"))
        refresh = style_button(Button(text="Refresh", size_hint_x=None, width=dp(120)), "secondary")
        refresh.bind(on_release=self.refresh)
        heading.add_widget(refresh)
        self.add_widget(heading)
        self.add_widget(
            caption_label("Runtime information and locally recorded application errors.")
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
        self.add_widget(self.health_summary)
        self.add_widget(section_label("Recent issues"))
        self._rows = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(6))
        self._rows.bind(minimum_height=self._rows.setter("height"))
        scroll = ScrollView(do_scroll_x=False, bar_width=dp(5))
        scroll.add_widget(self._rows)
        self.add_widget(scroll)
        self.refresh()

    def refresh(self, *_: object) -> None:
        health = self._health.snapshot()
        status = "Healthy" if health.database_healthy else "Unavailable"
        self.health_summary.text = (
            f"Project Planner {health.app_version}  ·  Kivy {kivy_version}  ·  "
            f"Python {health.python_version}\n"
            f"Database: {status} ({health.database_backend})\n"
            f"Location: {health.database_location}\n"
            f"Recorded issues: {health.issue_count}"
        )
        self.health_summary.color = PEARL_GREY if health.database_healthy else RED
        self._rows.clear_widgets()
        issues = self._issues.list_recent(50) if health.database_healthy else []
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
