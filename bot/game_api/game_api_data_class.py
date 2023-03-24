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
