from collections.abc import Callable

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.widget import Widget

from project_planner_frontend.projects.views.BinButton import BinButton
from project_planner_frontend.projects.views.DisclosureButton import DisclosureButton
from project_planner_frontend.projects.views.GearMenuButton import GearMenuButton
from project_planner_frontend.shared.theme import GOLD_LIGHT, SLATE_400, style_button


class ProjectCategoryRow(BoxLayout):
    def __init__(
        self,
        category_id: str | None,
        name: str,
        project_count: int,
        selected: bool,
        expanded: bool,
        on_select: Callable[[], None],
        on_toggle: Callable[[], None],
        on_add_project: Callable[[], None],
        on_rename: Callable[[], None] | None,
        on_delete: Callable[[], None] | None,
        **kwargs: object,
    ) -> None:
        super().__init__(size_hint_y=None, height=dp(40), spacing=dp(4), **kwargs)
        self.category_id = category_id
        self.disclosure_button = None
        if project_count:
            self.disclosure_button = style_button(DisclosureButton(expanded), "quiet")
            self.disclosure_button.bind(on_release=lambda *_: on_toggle())
            self.add_widget(self.disclosure_button)
        else:
            self.add_widget(Widget(size_hint_x=None, width=dp(34)))
        label = f"{name.upper()}  ·  {project_count}"
        self.button = style_button(
            Button(text=label, halign="left", valign="middle"),
            "selected" if selected else "secondary",
        )
        self.button.color = GOLD_LIGHT if not selected else self.button.color
        if name == "Uncategorized" and not selected:
            self.button.color = SLATE_400
        self.button.bind(
            size=lambda widget, size: setattr(widget, "text_size", (size[0] - dp(18), size[1]))
        )
        self.button.bind(on_release=lambda *_: on_select())
        self.add_widget(self.button)
        self.add_project_button = style_button(
            Button(
                text="+",
                size_hint=(None, None),
                size=(dp(34), dp(34)),
                pos_hint={"center_y": 0.5},
                font_size="18sp",
            ),
            "primary",
        )
        self.add_project_button.bind(on_release=lambda *_: on_add_project())
        self.add_widget(self.add_project_button)
        self.gear_button = None
        if on_rename is not None:
            self.gear_button = style_button(
                GearMenuButton((("Rename", on_rename, "secondary", False),)),
                "secondary",
            )
            self.add_widget(self.gear_button)
        self.delete_button = None
        if on_delete is not None:
            self.delete_button = style_button(BinButton(), "danger")
            self.delete_button.bind(on_release=lambda *_: on_delete())
            self.add_widget(self.delete_button)
