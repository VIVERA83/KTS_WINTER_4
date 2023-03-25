from dataclasses import dataclass, asdict


@dataclass
class BaseDataClass:
    @property
    def as_dict(self) -> dict:
        return asdict(self)


@dataclass
class GameSessionRequest(BaseDataClass):
    captain_id: int
    users: list[int]


@dataclass
class UserRequest(BaseDataClass):
    vk_user_id: int
    username: str


@dataclass
class Question(BaseDataClass):
    id: int
    title: str
    correct_answer: str
    rounds: list


@dataclass
class RoundRequest(BaseDataClass):
    respondent_id: int
    answer: str
    question_id: int
    game_session_id: int
