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
from project_planner_frontend.shared.date_parser import format_optional_date
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
        paint_background(self, NAVY_900)
        self._title = title_label("Free section")
        self.add_widget(self._title)
        self.add_widget(caption_label("Organize work without Agile or Waterfall terminology."))
        add = style_button(Button(text="+ Add item", size_hint_y=None, height=dp(44)), "primary")
        add.bind(on_release=self._add)
        self.add_widget(add)
        self._rows = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(6))
        self._rows.bind(minimum_height=self._rows.setter("height"))
        scroll = ScrollView(do_scroll_x=False)
        scroll.add_widget(self._rows)
        self.add_widget(scroll)

    def show_section(self, section_id: str) -> None:
        self._section_id = section_id
        self._title.text = self._sections.require(section_id).name
        self.refresh()

    def refresh(self) -> None:
        self._rows.clear_widgets()
        if self._section_id is None:
            return
        items = list(self._sections.list_items(self._section_id))
        if not items:
            self._rows.add_widget(
                Label(text="No items yet.", color=SLATE_400, size_hint_y=None, height=dp(54))
            )
        for item in items:
            row = BoxLayout(size_hint_y=None, height=dp(62), spacing=dp(5))
            status = item.status.value.replace("_", " ").title()
            item_date = format_optional_date(item.item_date) or "No date"
            edit = style_button(
                Button(
                    text=(
                        f"{item.title}\n{status} · {item.assignee or 'Unassigned'} · {item_date}"
                    ),
                    halign="left",
                ),
                "quiet",
            )
            edit.bind(on_release=partial(self._edit, item))
            up = style_button(Button(text="Up", size_hint_x=None, width=dp(58)), "secondary")
            down = style_button(Button(text="Down", size_hint_x=None, width=dp(58)), "secondary")
            up.bind(on_release=partial(self._move, item.id, -1))
            down.bind(on_release=partial(self._move, item.id, 1))
            remove = style_button(Button(text="Delete", size_hint_x=None, width=dp(76)), "danger")
            remove.bind(on_release=partial(self._remove, item.id))
            row.add_widget(edit)
            row.add_widget(up)
            row.add_widget(down)
            row.add_widget(remove)
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

    def _move(self, item_id: str, offset: int, *_: object) -> None:
        if self._section_id:
            self._sections.move_item(self._section_id, item_id, offset)
            self.refresh()

    def _remove(self, item_id: str, *_: object) -> None:
        self._sections.remove_item(item_id)
        self.refresh()
