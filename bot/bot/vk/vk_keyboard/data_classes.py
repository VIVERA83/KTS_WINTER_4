from dataclasses import asdict, dataclass, field
from enum import Enum


class TypeColor(Enum):
    blue = "primary"
    white = "secondary"
    red = "negative"
    green = "positive"


class TypeButton(Enum):
    callback = "callback"
    text = "text"


@dataclass
class Payload:
    data: dict = field(default_factory=dict)
    keyboard_name: str = None
    button_name: str = None

    @property
    def as_dict(self):
        return asdict(self)
