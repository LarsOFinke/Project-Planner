import argparse
import os
import time
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
        from kivy.uix.boxlayout import BoxLayout
        from kivy.uix.popup import Popup
        from project_planner_frontend.bootstrap.clipboard_bootstrap import configure_clipboard
        from project_planner_frontend.bootstrap.input_bootstrap import configure_mouse_input

        from project_planner.api.controller_builder import build_controllers
        from project_planner.modules.planning.entities.BacklogItem import BacklogItem
        from project_planner.modules.planning.entities.PlanningSection import PlanningSection
        from project_planner.modules.planning.entities.SectionType import SectionType
        from project_planner.shared.settings.Settings import Settings

        configure_clipboard()
        configure_mouse_input()

        from project_planner_frontend.application.ProjectPlannerApp import ProjectPlannerApp
        from project_planner_frontend.planning.views.agile.AgilePlanningPanel import (
            AgilePlanningPanel,
        )
        from project_planner_frontend.planning.views.custom.CustomPlanningPanel import (
            CustomPlanningPanel,
        )
        from project_planner_frontend.projects.views.ProjectTreeRow import ProjectTreeRow
        from project_planner_frontend.shared.SimpleTabbedPanel import SimpleTabbedPanel

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
        planning_layout_verified = False
        editor_verified = False
        tool_dock_verified = False
        rows_ready_at: float | None = None

        def layout_widgets(widget: object) -> None:
            do_layout = getattr(widget, "do_layout", None)
            if do_layout is not None:
                do_layout()
            for child_widget in reversed(getattr(widget, "children", ())):
                layout_widgets(child_widget)

        def exercise_drag_target(_elapsed: float) -> None:
            nonlocal drag_diagnostic, drag_target_verified, rows_ready_at
            planner = application._host._planner_root
            if planner is None:
                return
            rows = {
                row.project_id: row
                for row in planner.browser._list.children
                if isinstance(row, ProjectTreeRow)
            }
            if project.id not in rows or drop_target.id not in rows:
                Clock.schedule_once(exercise_drag_target, 0.1)
                return
            if rows_ready_at is None:
                rows_ready_at = time.monotonic()
            if time.monotonic() - rows_ready_at < 0.5:
                layout_widgets(application.root)
                Clock.schedule_once(exercise_drag_target, 0.1)
                return
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

            layout_widgets(application.root)
            source_position = visible_center(source.button)
            for step in range(101):
                scroll_y = 1 - step / 100
                scroll.scroll_y = scroll_y
                scroll.update_from_scroll()
                source_position = visible_center(source.button)
                if scroll.y <= source_position[1] <= scroll.top:
                    break
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
            edge_position = (scroll.center_x, scroll.top - 2)
            move_touch(touch, edge_position)
            for step in range(101):
                scroll.scroll_y = step / 100
                scroll.update_from_scroll()
                candidate = visible_center(target)
                if scroll.y <= candidate[1] <= scroll.top:
                    break
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

        def show_planning_examples(_elapsed: float) -> None:
            planner = application._host._planner_root
            if planner is None:
                return
            planner._admin_popup.dismiss()
            preview = BoxLayout(orientation="vertical")
            custom = CustomPlanningPanel(None, None, None, None, None, None)
            sections = [
                PlanningSection("preview", "Short", SectionType.FREE, 0),
                PlanningSection(
                    "preview",
                    "A much longer section title that should stay left aligned",
                    SectionType.AGILE,
                    1,
                ),
            ]
            custom._render(sections, custom._roadmap_rows[1], True)
            agile = AgilePlanningPanel(None)
            agile._backlog[1].add_widget(agile._item_row(BacklogItem("preview", "Short", 0)))
            agile._backlog[1].add_widget(
                agile._item_row(BacklogItem("preview", "A much longer backlog title", 1))
            )
            preview.add_widget(custom)
            preview.add_widget(agile)
            popup = Popup(title="Planning layout smoke", content=preview, size_hint=(0.95, 0.9))
            popup.open()

            def verify(_elapsed: float) -> None:
                nonlocal planning_layout_verified
                agile_tabs = next(
                    child for child in agile.children if isinstance(child, SimpleTabbedPanel)
                )
                agile_tabs.switch_to(agile_tabs._headers[0])
                layout_widgets(popup)
                agile._backlog[0].width = agile.width
                agile._backlog[1].width = agile.width
                layout_widgets(agile._backlog[0])
                groups = (custom._roadmap_rows[1].children, agile._backlog[1].children)
                for rows in groups:
                    summaries = [
                        next(
                            child
                            for child in row.children
                            if isinstance(child, BoxLayout)
                            and any(isinstance(part, BoxLayout) for part in child.children)
                        )
                        for row in rows
                    ]
                    titles = [summary.children[1] for summary in summaries]
                    if any(title.halign != "left" or title.text_size[0] <= 0 for title in titles):
                        details = [
                            (title.text, title.halign, title.text_size, title.size)
                            for title in titles
                        ]
                        raise AssertionError(f"Planning titles are not left aligned: {details}")
                    first_columns = [summary.children[0].children[-1].x for summary in summaries]
                    if max(first_columns) - min(first_columns) > 1:
                        raise AssertionError("Planning metadata columns do not align")
                planning_layout_verified = True
                popup.dismiss()

            Clock.schedule_once(verify, 0.4)

        def exercise_editors(_elapsed: float) -> None:
            nonlocal editor_verified
            from project_planner_frontend.artifacts.views.diagram.DiagramCanvas import (
                DiagramCanvas,
            )
            from project_planner_frontend.artifacts.views.workspace.FreehandCanvas import (
                FreehandCanvas,
            )

            preview = BoxLayout(orientation="vertical")
            workspace = FreehandCanvas(lambda: None)
            diagram = DiagramCanvas(lambda: None)
            preview.add_widget(workspace)
            preview.add_widget(diagram)
            popup = Popup(title="Editor geometry smoke", content=preview, size_hint=(0.9, 0.8))
            popup.open()

            def verify(_elapsed: float) -> None:
                nonlocal editor_verified
                layout_widgets(popup)
                shape_id = workspace.add_shape("rectangle", pos=(40, 60))
                workspace.add_text("Project note", pos=(80, 120))
                first_id = diagram.add_node("Start", pos=(40, 60))
                second_id = diagram.add_node("Finish", pos=(280, 160))
                diagram._clear_selection()
                diagram._select(first_id)
                diagram._select(second_id)
                diagram.connect_selected()
                workspace._select(shape_id)
                workspace.set_selected_geometry(100, 120, 200, 100)
                diagram._select(first_id)
                diagram.set_selected_geometry(100, 120, 200, 100)
                before_workspace = workspace.to_document()
                before_diagram = diagram.to_document()
                workspace.zoom_by(1.25)
                workspace.pan_by(40, -20)
                diagram.zoom_by(1.25)
                diagram.pan_by(-40, 20)
                workspace.pos = workspace.x + 12, workspace.y + 8
                diagram.pos = diagram.x + 12, diagram.y + 8
                assert workspace.to_document() == before_workspace
                assert diagram.to_document() == before_diagram
                assert tuple(workspace._elements[shape_id].pos) == workspace._transform.to_screen(
                    100, 120
                )
                assert tuple(diagram._nodes[first_id].pos) == diagram._transform.to_screen(100, 120)
                workspace.clear_drawing()
                assert workspace.undo() and workspace.to_document() == before_workspace
                assert workspace.redo() and not workspace.to_document().shapes
                diagram.clear_diagram()
                assert diagram.undo() and diagram.to_document() == before_diagram
                editor_verified = True
                popup.dismiss()

            Clock.schedule_once(verify, 0.3)

        def show_tool_docks(_elapsed: float) -> None:
            planner = application._host._planner_root
            planner.tabs.switch_to(planner._tab_headers[3])

            def verify_workspace(_elapsed: float) -> None:
                layout_widgets(application.root)
                panel = planner.workspace
                panel.toolbox._scroll.update_from_scroll()
                size_button = panel.toolbox.button("Quick edit", "Size +")
                shape_button = panel.toolbox.button("Quick edit", "Rectangle")
                if panel.toolbox.x >= panel.canvas_editor.x:
                    raise AssertionError("Workspace dock is not beside the canvas")
                visible_y = size_button.center_y + panel.toolbox._scroll.g_translate.y
                if not panel.toolbox._scroll.y <= visible_y <= panel.toolbox._scroll.top:
                    raise AssertionError(
                        "Workspace size control is not initially visible: "
                        f"button={size_button.pos, size_button.size}, "
                        f"scroll={panel.toolbox._scroll.pos, panel.toolbox._scroll.size}, "
                        f"scroll_y={panel.toolbox._scroll.scroll_y}, "
                        f"translate={panel.toolbox._scroll.g_translate.xy}, "
                        f"stack={panel.toolbox._scroll.children[0].pos}, "
                        f"canvas={panel.canvas_editor.pos, panel.canvas_editor.size}"
                    )
                shape_y = shape_button.center_y + panel.toolbox._scroll.g_translate.y
                if not panel.toolbox._scroll.y <= shape_y <= panel.toolbox._scroll.top:
                    raise AssertionError("Workspace rectangle tool is not initially visible")
                planner.tabs.switch_to(planner._tab_headers[2])
                Clock.schedule_once(verify_diagram, 0.2)

            def verify_diagram(_elapsed: float) -> None:
                nonlocal tool_dock_verified
                layout_widgets(application.root)
                panel = planner.diagram
                panel.toolbox._scroll.update_from_scroll()
                geometry_button = panel.toolbox.button("Quick edit", "Geometry")
                if panel.toolbox.x >= panel.canvas_editor.x:
                    raise AssertionError("Diagram dock is not beside the canvas")
                visible_y = geometry_button.center_y + panel.toolbox._scroll.g_translate.y
                if not panel.toolbox._scroll.y <= visible_y <= panel.toolbox._scroll.top:
                    raise AssertionError("Diagram geometry control is not initially visible")
                tool_dock_verified = True

            Clock.schedule_once(verify_workspace, 0.2)

        Clock.schedule_once(lambda _elapsed: layout_widgets(application.root), 0.1)
        Clock.schedule_once(lambda _elapsed: layout_widgets(application.root), 0.35)
        Clock.schedule_once(exercise_drag_target, 0.75)
        Clock.schedule_once(show_admin, 1.0)
        Clock.schedule_once(show_planning_examples, 2.0)
        Clock.schedule_once(exercise_editors, 3.0)
        Clock.schedule_once(show_tool_docks, 3.7)
        Clock.schedule_once(lambda _elapsed: application.stop(), 5.0)
        application.run()
        if not drag_target_verified:
            raise AssertionError(f"Rendered project drag failed: {drag_diagnostic}")
        if not planning_layout_verified:
            raise AssertionError("Planning layouts were not verified in the event loop")
        if not editor_verified:
            raise AssertionError("Editor geometry was not verified in the event loop")
        if not tool_dock_verified:
            raise AssertionError("Editor tool docks were not verified in the event loop")


if __name__ == "__main__":
    main()
