import json
from typing import Optional

from icecream import ic

from .buttons import TYPE_BUTTON


class Keyboard:
    def __init__(
        self,
        name: str,
        buttons: Optional[dict[int, list[TYPE_BUTTON]]],
        one_time: bool = True,
    ):
        self.name = name
        self.one_time = one_time
        self.buttons = buttons

    @property
    def as_dict(self) -> dict:
        keyboard_buttons = []
        for buttons in self.buttons.values():
            layout = []
            for button in buttons:
                button.payload.keyboard_name = self.name
                layout.append(button.as_dict())
            keyboard_buttons.append(layout)
        return {"one_time": self.one_time, "buttons": keyboard_buttons}

    @property
    def as_str(self) -> str:
        return json.dumps(self.as_dict)

    def get_help_string_from_title(self, title_name: str) -> str:
        """Вытаскиваем из кнопки ее строчку, которая заготовлена при объявлении клавиатуры"""
        for buttons in self.buttons.values():
            for button in buttons:
                if button.name == title_name:
                    return button.help_string

    def __str__(self):
        return f"Keyboard({repr(self.name)})"

    __repr__ = __str__
