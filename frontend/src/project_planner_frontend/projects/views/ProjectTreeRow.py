from collections.abc import Callable
from math import hypot

from kivy.graphics import Color, Line
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.widget import Widget

from project_planner_frontend.projects.views.BinButton import BinButton
from project_planner_frontend.projects.views.DisclosureButton import DisclosureButton
from project_planner_frontend.projects.views.GearMenuButton import GearMenuButton
from project_planner_frontend.shared.theme import BORDER, RED, SLATE_200, style_button


class ProjectTreeRow(BoxLayout):
    """A project row whose entire control is offset to express hierarchy."""

    def __init__(
        self,
        project_id: str,
        title: str,
        status: str,
        depth: int,
        selected: bool,
        has_children: bool,
        expanded: bool,
        on_select: Callable[[], None],
        on_drop: Callable[[tuple[float, float]], None],
        on_toggle: Callable[[], None],
        on_add_child: Callable[[], None],
        on_archive: Callable[[], None],
        on_delete: Callable[[], None],
        **kwargs: object,
    ) -> None:
        super().__init__(size_hint_y=None, height=dp(54), spacing=dp(4), **kwargs)
        self.project_id = project_id
        self._on_drop = on_drop
        self._drag_origin: tuple[float, float] | None = None
        self._dragging = False
        self._depth = max(0, depth)
        self._indent_width = dp(12 * min(self._depth, 6))
        branch = Widget(size_hint_x=None, width=self._indent_width)
        self.add_widget(branch)
        self.disclosure_button = None
        if has_children:
            self.disclosure_button = style_button(DisclosureButton(expanded), "quiet")
            self.disclosure_button.bind(on_release=lambda *_: on_toggle())
            self.add_widget(self.disclosure_button)
        else:
            self.add_widget(Widget(size_hint_x=None, width=dp(34)))
        self.drag_handle = style_button(
            Button(
                text="↕",
                size_hint=(None, None),
                size=(dp(34), dp(34)),
                pos_hint={"center_y": 0.5},
                font_size="17sp",
            ),
            "quiet",
        )
        self.add_widget(self.drag_handle)
        self.button = style_button(
            Button(
                text=f"{title}\n{status.replace('_', ' ').title()}",
                halign="left",
                valign="middle",
            ),
            "selected" if selected else "quiet",
        )
        if status == "blocked" and not selected:
            self.button.color = RED
        elif not selected:
            self.button.color = SLATE_200
        self.button.bind(
            size=lambda widget, size: setattr(
                widget,
                "text_size",
                (size[0] - dp(20), size[1]),
            )
        )
        self.button.bind(on_release=lambda *_: on_select())
        self.add_widget(self.button)
        archived = status == "archived"
        archive_label = "Archived" if archived else "Archive"
        self.gear_button = style_button(
            GearMenuButton(
                (
                    ("Add child", on_add_child, "secondary", False),
                    (archive_label, on_archive, "secondary", archived),
                )
            ),
            "secondary",
        )
        self.add_widget(self.gear_button)
        self.delete_button = style_button(BinButton(), "danger")
        self.delete_button.bind(on_release=lambda *_: on_delete())
        self.add_widget(self.delete_button)
        with self.canvas.before:
            self._branch_color = Color(*BORDER)
            self._branch_line = Line(points=[], width=1.1)
        self.bind(pos=self._sync_branch, size=self._sync_branch)
        self._sync_branch()

    def on_touch_down(self, touch: object) -> bool:
        if getattr(touch, "button", "left") == "left" and self.drag_handle.collide_point(
            *touch.pos
        ):
            self._drag_origin = touch.pos
            self._dragging = False
            self.drag_handle.state = "down"
            touch.grab(self)
            return True
        return super().on_touch_down(touch)

    def on_touch_move(self, touch: object) -> bool:
        if touch.grab_current is self and self._drag_origin is not None:
            if hypot(touch.x - self._drag_origin[0], touch.y - self._drag_origin[1]) >= dp(8):
                self._dragging = True
                self.drag_handle.opacity = 0.65
            return True
        return super().on_touch_move(touch)

    def on_touch_up(self, touch: object) -> bool:
        if touch.grab_current is self:
            touch.ungrab(self)
            self.drag_handle.state = "normal"
            self.drag_handle.opacity = 1
            if self._dragging:
                self._on_drop(touch.pos)
            self._drag_origin = None
            self._dragging = False
            return True
        return super().on_touch_up(touch)

    def _sync_branch(self, *_: object) -> None:
        if self._depth == 0:
            self._branch_line.points = []
            return
        anchor_x = self.x + self._indent_width - dp(6)
        self._branch_line.points = [
            anchor_x,
            self.y,
            anchor_x,
            self.top,
            anchor_x,
            self.center_y,
            self.x + self._indent_width + dp(2),
            self.center_y,
        ]
