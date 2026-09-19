from collections.abc import Callable
from math import hypot

from kivy.core.window import Window
from kivy.graphics import Color, Line, PopMatrix, PushMatrix, Translate
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.widget import Widget

from project_planner_frontend.projects.views.BinButton import BinButton
from project_planner_frontend.projects.views.DisclosureButton import DisclosureButton
from project_planner_frontend.projects.views.GearMenuButton import GearMenuButton
from project_planner_frontend.shared.theme import (
    BORDER,
    GOLD_LIGHT,
    SLATE_200,
    style_button,
)


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
        on_drag: Callable[[tuple[float, float] | None], None],
        on_drop: Callable[[tuple[float, float]], None],
        on_toggle: Callable[[], None],
        on_add_child: Callable[[], None],
        on_archive: Callable[[], None],
        on_delete: Callable[[], None],
        **kwargs: object,
    ) -> None:
        super().__init__(size_hint_y=None, height=dp(54), spacing=dp(4), **kwargs)
        self.project_id = project_id
        self._on_select = on_select
        self._on_drag = on_drag
        self._on_drop = on_drop
        self._drag_touch: object | None = None
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
        status_color = {
            "idea": "#A8B4C2",
            "planned": "#E0C17C",
            "active": "#69A987",
            "blocked": "#CE6A6A",
            "completed": "#A8B4C2",
            "archived": "#52657A",
        }.get(status, "#A8B4C2")
        status_label = status.replace("_", " ").title()
        self.button = style_button(
            Button(
                text=(
                    f"[b][color={status_color}]{status_label}[/color][/b] "
                    f"[color=#52657A]│[/color] {title}"
                ),
                markup=True,
                halign="left",
                valign="middle",
            ),
            "selected" if selected else "quiet",
        )
        if not selected:
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
            PushMatrix()
            self._drag_translation = Translate(0, 0)
            self._branch_color = Color(*BORDER)
            self._branch_line = Line(points=[], width=1.1)
        with self.canvas.after:
            self._drop_target_color = Color(*GOLD_LIGHT[:3], 0)
            self._drop_target_outline = Line(
                rounded_rectangle=(0, 0, 0, 0, dp(7)),
                width=dp(1.6),
            )
            PopMatrix()
        self.bind(pos=self._sync_visuals, size=self._sync_visuals)
        self._sync_visuals()

    def on_touch_down(self, touch: object) -> bool:
        action_controls = [self.gear_button, self.delete_button]
        if self.disclosure_button is not None:
            action_controls.append(self.disclosure_button)
        touches_action = any(control.collide_point(*touch.pos) for control in action_controls)
        if (
            getattr(touch, "button", "left") == "left"
            and self.collide_point(*touch.pos)
            and not touches_action
        ):
            self._drag_touch = touch
            self._drag_origin = self._window_position(touch)
            self._dragging = False
            self.button.state = "down"
            touch.grab(self)
            return True
        return super().on_touch_down(touch)

    def on_touch_move(self, touch: object) -> bool:
        if touch is self._drag_touch and self._drag_origin is not None:
            position = self._window_position(touch)
            if hypot(
                position[0] - self._drag_origin[0],
                position[1] - self._drag_origin[1],
            ) >= dp(8):
                self._dragging = True
            if self._dragging:
                self.opacity = 0.68
                self._drag_translation.y = position[1] - self._drag_origin[1]
                self._on_drag(position)
            return True
        return super().on_touch_move(touch)

    def on_touch_up(self, touch: object) -> bool:
        if touch is self._drag_touch:
            position = self._window_position(touch)
            touch.ungrab(self)
            self.button.state = "normal"
            self.opacity = 1
            self._drag_translation.y = 0
            if self._dragging:
                self._on_drag(None)
                self._on_drop(position)
            else:
                self._on_select()
            self._drag_touch = None
            self._drag_origin = None
            self._dragging = False
            return True
        return super().on_touch_up(touch)

    @staticmethod
    def _window_position(touch: object) -> tuple[float, float]:
        if hasattr(touch, "sx") and hasattr(touch, "sy"):
            return (touch.sx * Window.width, touch.sy * Window.height)
        return touch.pos

    def set_drop_target(self, active: bool) -> None:
        self._drop_target_color.a = 1 if active else 0

    def _sync_visuals(self, *_: object) -> None:
        self._sync_branch()
        inset = dp(1)
        self._drop_target_outline.rounded_rectangle = (
            self.x + inset,
            self.y + inset,
            max(0, self.width - inset * 2),
            max(0, self.height - inset * 2),
            dp(7),
        )

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
