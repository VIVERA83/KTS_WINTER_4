from typing import Optional, Union

from .data_classes import Payload, TypeButton, TypeColor

TYPE_BUTTON = Union["Button", "Title"]


class Base:
    # имя кнопки
    name: str
    # подпись кнопки, видимая в ВК
    label: str
    # текущий цвет кнопки
    color: Optional[TypeColor] = None
    # тип кнопки, по сути их 2
    type_button: Optional[TypeButton] = None
    # Полезная нагрузка на кнопку, которая будет передаваться после нажатие на нее обратно
    payload: Optional[Payload] = None

    # цвет кнопки, активное состояние
    active: Optional[TypeColor] = None
    # цвет кнопки, пассивное состояние
    passive: Optional[TypeColor] = None

    def as_dict(self):
        return {
            "action": {
                "type": self.type_button.value,
                "label": self.label,
                "payload": self.payload.as_dict,
            },
            "color": self.color.value,
        }

    def __str__(self):
        return f"{self.__class__.__name__}(name={self.name} label={self.label})"

    __repr__ = __str__


class Title(Base):
    def __init__(
        self,
        name: str,
        label: str,
        color: TypeColor,
        help_string: str,
        keyboard_name: Optional[str] = None,
    ):
        self.type_button = TypeButton.callback
        self.name = name
        self.label = label
        self.color = color
        self.help_string = help_string
        self.keyboard_name = keyboard_name
        self.payload = Payload(button_name=self.name, data={"text": help_string})


class Button(Base):
    def __init__(
        self,
        name: str,
        label: str,
        color: TypeColor,
    ):
        self.type_button = TypeButton.text
        self.name = name
        self.label = label
        self.color = color
        self.payload = Payload(button_name=self.name)
