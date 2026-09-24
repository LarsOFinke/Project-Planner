from project_planner_frontend.artifacts.views.diagram.DiagramToolbox import DiagramToolbox
from project_planner_frontend.artifacts.views.workspace.WorkspaceToolbox import WorkspaceToolbox


def test_workspace_quick_tools_follow_selection() -> None:
    def noop(*_: object) -> None:
        pass

    toolbox = WorkspaceToolbox(
        add_shape=noop,
        choose_image=noop,
        add_text=noop,
        edit_text=noop,
        edit_geometry=noop,
        rotate=noop,
        scale=noop,
        zoom=noop,
        pan=noop,
        toggle_snap=noop,
        undo=noop,
        redo=noop,
        set_color=noop,
        set_mode=noop,
        delete_selected=noop,
        clear_all=noop,
        save=noop,
    )
    assert toolbox.button("Quick edit", "Size +").disabled
    assert toolbox.button("Quick edit", "Rectangle").disabled is False
    toolbox.set_selection("rectangle")
    assert toolbox.button("Quick edit", "Size +").disabled is False
    assert toolbox.button("Object details", "Rotate +").disabled is False
    toolbox.set_selection("text")
    assert toolbox.button("Object details", "Rotate +").disabled
    assert toolbox.button("Object details", "Edit text").disabled is False


def test_diagram_connection_tool_requires_two_selected_nodes() -> None:
    def noop(*_: object) -> None:
        pass

    toolbox = DiagramToolbox(
        add_node=noop,
        rename_node=noop,
        edit_geometry=noop,
        connect_selected=noop,
        zoom=noop,
        pan=noop,
        toggle_snap=noop,
        undo=noop,
        redo=noop,
        delete_selected=noop,
        clear_all=noop,
        save=noop,
    )
    assert toolbox.button("Quick edit", "Connect").disabled
    toolbox.set_selection(1)
    assert toolbox.button("Quick edit", "Geometry").disabled is False
    toolbox.set_selection(2)
    assert toolbox.button("Quick edit", "Connect").disabled is False
    assert toolbox.button("Quick edit", "Geometry").disabled
