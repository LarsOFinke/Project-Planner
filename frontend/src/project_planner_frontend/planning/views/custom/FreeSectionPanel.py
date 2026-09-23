from datetime import date
from functools import partial

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView

from project_planner.modules.planning.entities.SectionItem import SectionItem
from project_planner.modules.planning.entities.SectionStatus import SectionStatus
from project_planner_frontend.planning.clients.SectionClient import SectionClient
from project_planner_frontend.planning.views.custom.SectionItemEditorPopup import (
    SectionItemEditorPopup,
)
from project_planner_frontend.planning.views.planning_summary import planning_summary
from project_planner_frontend.shared.date_parser import format_optional_date
from project_planner_frontend.shared.ReorderableRow import ReorderableRow
from project_planner_frontend.shared.theme import (
    NAVY_900,
    SLATE_400,
    caption_label,
    paint_background,
    style_button,
    title_label,
)


class FreeSectionPanel(BoxLayout):
    def __init__(self, sections: SectionClient, **kwargs: object) -> None:
        super().__init__(orientation="vertical", spacing=dp(8), padding=dp(10), **kwargs)
        self._sections = sections
        self._section_id: str | None = None
        self._drop_target_row: ReorderableRow | None = None
        paint_background(self, NAVY_900)
        self._title = title_label("Free section")
        self.add_widget(self._title)
        self.add_widget(
            caption_label("Organize work freely; drag an item onto another to reorder.")
        )
        add = style_button(Button(text="+ Add item", size_hint_y=None, height=dp(44)), "primary")
        add.bind(on_release=self._add)
        self.add_widget(add)
        self._rows = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(6))
        self._rows.bind(minimum_height=self._rows.setter("height"))
        self._scroll = ScrollView(do_scroll_x=False)
        self._scroll.add_widget(self._rows)
        self.add_widget(self._scroll)

    def show_section(self, section_id: str) -> None:
        self._section_id = section_id
        self._title.text = self._sections.require(section_id).name
        self.refresh()

    def refresh(self) -> None:
        self._clear_drop_target()
        self._rows.clear_widgets()
        if self._section_id is None:
            return
        items = list(self._sections.list_items(self._section_id))
        if not items:
            self._rows.add_widget(
                Label(text="No items yet.", color=SLATE_400, size_hint_y=None, height=dp(54))
            )
        for item in items:
            row = ReorderableRow(
                item.id,
                partial(self._edit, item),
                self._drag_item,
                self._drop_item,
                size_hint_y=None,
                height=dp(84),
                spacing=dp(5),
            )
            status = item.status.value.replace("_", " ").title()
            item_date = format_optional_date(item.item_date) or "No date"
            summary, edit = planning_summary(
                item.title,
                (
                    ("Status", status, 0.3),
                    ("Assignee", item.assignee or "Unassigned", 0.4),
                    ("Date", item_date, 0.3),
                ),
            )
            remove = style_button(Button(text="Delete", size_hint_x=None, width=dp(76)), "danger")
            remove.bind(on_release=partial(self._remove, item.id))
            row.add_widget(summary)
            row.add_widget(remove)
            row.set_primary_control(edit)
            row.register_action_controls((remove,))
            self._rows.add_widget(row)

    def _add(self, *_: object) -> None:
        if self._section_id:
            SectionItemEditorPopup(None, self._create).open()

    def _create(
        self,
        title: str,
        description: str,
        assignee: str,
        status: SectionStatus,
        item_date: date | None,
    ) -> None:
        if self._section_id:
            self._sections.add_item(
                self._section_id, title, description, assignee, status, item_date
            )
            self.refresh()

    def _edit(self, item: SectionItem, *_: object) -> None:
        def save(
            title: str,
            description: str,
            assignee: str,
            status: SectionStatus,
            item_date: date | None,
        ) -> None:
            self._sections.update_item(
                item,
                title=title,
                description=description,
                assignee=assignee,
                status=status,
                item_date=item_date,
            )
            self.refresh()

        SectionItemEditorPopup(item, save).open()

    def _drag_item(self, item_id: str, position: tuple[float, float] | None) -> None:
        target = None if position is None else self._drop_target_at(item_id, position)
        if target is self._drop_target_row:
            return
        self._clear_drop_target()
        self._drop_target_row = target
        if target is not None:
            target.set_drop_target(True)

    def _drop_item(self, item_id: str, position: tuple[float, float]) -> None:
        target = self._drop_target_at(item_id, position)
        self._clear_drop_target()
        if target is not None and self._section_id:
            self._sections.move_item_to(self._section_id, item_id, target.item_id)
            self.refresh()

    def _drop_target_at(self, item_id: str, position: tuple[float, float]) -> ReorderableRow | None:
        if not self._scroll.collide_point(*position):
            return None
        list_position = self._rows.to_widget(*position)
        return next(
            (
                row
                for row in self._rows.children
                if isinstance(row, ReorderableRow)
                and row.item_id != item_id
                and row.collide_point(*list_position)
            ),
            None,
        )

    def _clear_drop_target(self) -> None:
        if self._drop_target_row is not None:
            self._drop_target_row.set_drop_target(False)
        self._drop_target_row = None

    def _remove(self, item_id: str, *_: object) -> None:
        self._sections.remove_item(item_id)
        self.refresh()
