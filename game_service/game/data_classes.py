from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from game.models import GameSessionModel, RoundModel, UserModel


@dataclass
class BaseDataClass:
    @property
    def as_dict(self) -> dict:
        return asdict(self)


@dataclass
class UserRequest(BaseDataClass):
    vk_user_id: int
    username: Optional[str] = None


@dataclass
class UserIdRequest(BaseDataClass):
    id: int


@dataclass
class GameSessionRequest(BaseDataClass):
    captain_id: int
    users: list[int]


# models dataclasses
@dataclass
class User(BaseDataClass):
    id: int
    vk_user_id: int
    username: str
    game_sessions: list["GameSessionModel"]
    rounds: list["RoundModel"]


@dataclass
class GameSession(BaseDataClass):
    id: int
    captain_id: int
    users: list["User"]
    rounds: list["Round"]


# Question
@dataclass
class Question(BaseDataClass):
    id: int
    title: str
    correct_answer: str
    rounds: list["RoundModel"]


@dataclass
class QuestionRequest(BaseDataClass):
    title: str
    correct_answer: str


# Round
@dataclass
class Round(BaseDataClass):
    id: int
    answer: str
    round_number: int
    is_correct: bool
    respondent: "User"
    respondent_id: int
    question_id: int
    game_session_id: int


@dataclass
class RoundRequest(BaseDataClass):
    respondent_id: int
    answer: str
    question_id: int
    game_session_id: int


@dataclass
class RoundData(BaseDataClass):
    answer: str
    round_number: int
    is_correct: bool
    respondent_id: int
    question_id: int
    game_session_id: int
