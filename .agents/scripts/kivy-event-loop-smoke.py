import argparse
import os
from pathlib import Path
from tempfile import TemporaryDirectory


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scale", type=float, required=True)
    parser.add_argument("--width", type=int, required=True)
    parser.add_argument("--height", type=int, required=True)
    args = parser.parse_args()
    with (
        TemporaryDirectory(prefix="project-planner-kivy-home-") as kivy_home,
        TemporaryDirectory(prefix="project-planner-kivy-smoke-") as temporary,
    ):
        os.environ["KIVY_NO_ARGS"] = "1"
        os.environ["KIVY_HOME"] = kivy_home
        from kivy.clock import Clock
        from kivy.core.window import Window
        from kivy.input.providers.mouse import MouseMotionEvent
        from project_planner_frontend.bootstrap.clipboard_bootstrap import configure_clipboard
        from project_planner_frontend.bootstrap.input_bootstrap import configure_mouse_input

        from project_planner.api.controller_builder import build_controllers
        from project_planner.shared.settings.Settings import Settings

        configure_clipboard()
        configure_mouse_input()

        from project_planner_frontend.application.ProjectPlannerApp import ProjectPlannerApp
        from project_planner_frontend.projects.views.ProjectTreeRow import ProjectTreeRow

        root = Path(temporary)
        settings = Settings(
            database_path=root / "planner.sqlite3",
            data_directory=root / "data",
            window_width=args.width,
            window_height=args.height,
            autosave_seconds=20,
            ui_scale=args.scale,
            fullscreen=False,
        )
        projects, _planning, _collaboration, _artifacts, _system = build_controllers(settings)
        category = projects.create_category("Smoke category")
        project = projects.create_project("Smoke project", category_id=category.id)
        child = projects.create_project(
            "Nested smoke project",
            parent_id=project.id,
            category_id=category.id,
        )
        deep = projects.create_project(
            "Deep smoke project",
            parent_id=child.id,
            category_id=category.id,
        )
        target_category = projects.create_category("Target smoke category")
        drop_target = projects.create_project(
            "Zulu drop target",
            category_id=target_category.id,
        )
        application = ProjectPlannerApp(settings)
        drag_target_verified = False
        drag_diagnostic = "drag callback did not run"

        def layout_widgets(widget: object) -> None:
            do_layout = getattr(widget, "do_layout", None)
            if do_layout is not None:
                do_layout()
            for child_widget in reversed(getattr(widget, "children", ())):
                layout_widgets(child_widget)

        def exercise_drag_target(_elapsed: float) -> None:
            nonlocal drag_diagnostic, drag_target_verified
            planner = application._host._planner_root
            if planner is None:
                return
            rows = {
                row.project_id: row
                for row in planner.browser._list.children
                if isinstance(row, ProjectTreeRow)
            }
            source = rows[project.id]
            target = rows[drop_target.id]
            scroll = planner.browser._scroll

            def visible_center(widget: object) -> tuple[float, float]:
                translate_x, translate_y = scroll.g_translate.xy
                return widget.center_x + translate_x, widget.center_y + translate_y

            def move_touch(touch: MouseMotionEvent, position: tuple[float, float]) -> None:
                touch.move(
                    (
                        position[0] / Window.width,
                        position[1] / Window.height,
                        "left",
                    )
                )
                touch.scale_for_screen(Window.width, Window.height)
                for grabbed_reference in touch.grab_list[:]:
                    grabbed = grabbed_reference()
                    if grabbed is None:
                        continue
                    touch.grab_current = grabbed
                    grabbed.on_touch_move(touch)
                touch.grab_current = None

            scroll.update_from_scroll()
            layout_widgets(application.root)
            scroll.update_from_scroll()
            source_position = visible_center(source.button)
            touch = MouseMotionEvent(
                "mouse",
                "drag-smoke",
                (
                    source_position[0] / Window.width,
                    source_position[1] / Window.height,
                    "left",
                ),
                is_touch=True,
            )
            touch.scale_for_screen(Window.width, Window.height)
            scroll.on_touch_down(touch)
            row_received_touch = source._drag_touch is touch
            edge_position = (scroll.center_x, scroll.y + 2)
            for _step in range(32):
                move_touch(touch, edge_position)
                scroll.update_from_scroll()
            target_position = visible_center(target)
            move_touch(touch, target_position)
            target_highlighted = (
                planner.browser._drop_target_widget is target and target._drop_target_color.a == 1
            )
            source_translated = source._drag_translation.y != 0
            touch.update_time_end()
            for grabbed_reference in touch.grab_list[:]:
                grabbed = grabbed_reference()
                if grabbed is None:
                    continue
                touch.grab_current = grabbed
                grabbed.on_touch_up(touch)
            touch.grab_current = None
            persisted = projects.get_project(project.id)
            persisted_child = projects.get_project(child.id)
            persisted_deep = projects.get_project(deep.id)
            drag_target_verified = (
                row_received_touch
                and source_translated
                and target_highlighted
                and persisted.parent_id == drop_target.id
                and persisted.category_id == target_category.id
                and persisted_child.category_id == target_category.id
                and persisted_deep.category_id == target_category.id
            )
            drag_diagnostic = (
                f"row_touch={row_received_touch}, translated={source_translated}, "
                f"highlighted={target_highlighted}, parent={persisted.parent_id!r}, "
                f"expected={drop_target.id!r}, category={persisted.category_id!r}, "
                f"target_category={target_category.id!r}, target={target_position!r}, "
                f"source={source_position!r}, source_center={source.center!r}, "
                f"translate={scroll.g_translate.xy!r}, scroll_pos={scroll.pos!r}, "
                f"scroll_size={scroll.size!r}, scroll_y={scroll.scroll_y}"
            )

        def show_admin(_elapsed: float) -> None:
            planner = application._host._planner_root
            if planner is None:
                raise AssertionError("Project Planner root was not built")
            planner.admin_button.dispatch("on_release")

        Clock.schedule_once(lambda _elapsed: layout_widgets(application.root), 0.1)
        Clock.schedule_once(lambda _elapsed: layout_widgets(application.root), 0.35)
        Clock.schedule_once(exercise_drag_target, 0.75)
        Clock.schedule_once(show_admin, 1.0)
        Clock.schedule_once(lambda _elapsed: application.stop(), 1.6)
        application.run()
        if not drag_target_verified:
            raise AssertionError(f"Rendered project drag failed: {drag_diagnostic}")


if __name__ == "__main__":
    main()
