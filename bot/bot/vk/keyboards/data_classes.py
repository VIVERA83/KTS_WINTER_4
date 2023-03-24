from typing import TYPE_CHECKING, Type, Union
from dataclasses import dataclass, asdict, field

from pamqp import body

if TYPE_CHECKING:
    from bot.workers.keyboard import Keyboard


@dataclass
class BaseDataClass:
    @property
    def as_dict(self) -> dict:
        return asdict(self)


@dataclass()
class Data:
    value: Union[int, str, bool, dict]
    row: int
    button_name: str


@dataclass
class TimeoutKeyboard:
    keyboard: Type["Keyboard"]
    user_ids: list[int]
    keyboards: list[str] = None
    is_dynamic: bool = False
    is_private: bool = False
    body: str = "Переход в связи с окончанием времени"
    settings: "GameSessionSettings" = None,

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass
class GameSessionSettings(BaseDataClass):
    players: "Data"
    rounds: "Data"

    @property
    def get_rows(self) -> dict[str, int]:
        return {
            self.rounds.button_name: self.rounds.row,
            self.players.button_name: self.players.row,
        }


@dataclass
class TeamIsReady(BaseDataClass):
    buttons: dict[str, Union[bool, "Data"]] = field(default_factory=dict)

    @property
    def get_rows(self) -> dict[str, bool]:
        return {button_name: row for button_name, row in self.buttons}


@dataclass
class Round:
    number: int = 0
    users: dict[str, "Data"] = field(default_factory=dict)
    answers: dict[str, "Data"] = field(default_factory=dict)
    votes: dict[str, "Data"] = field(default_factory=dict)
    session_setting: GameSessionSettings = None
    # TODO на будущие
    game_session_id: int = False
    capitan: int = None
    question_id: int = None
    question: str = None
    correct_answer: str = None
    answer: str = None
    watcher: int = 0
    experts: int = 0
