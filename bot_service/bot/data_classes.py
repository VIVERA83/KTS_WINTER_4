import pickle
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Optional


class TypeMessage(Enum):
    message_new = "message_new"
    message_event = "message_event"
    message_reply = "message_reply"
    message_edit = "message_edit"


@dataclass
class MessageFromVK:
    user_id: int
    body: str
    type: TypeMessage
    payload: Optional["Payload"] = None
    event_id: str = None
    peer_id: int = None
    event_data: str = None

    @property
    def as_dict(self):
        return {
            "user_id": self.user_id,
            "body": self.body,
            "payload": self.payload.as_dict if self.payload else None,
            "type": self.type.value,
            "event_id": self.event_id,
            "peer_id": self.peer_id,
            "event_data": self.event_data,
        }


@dataclass
class Payload:
    keyboard_name: Optional[str] = None
    button_name: Optional[str] = None

    @property
    def as_dict(self):
        return asdict(self)


@dataclass
class MessageToVK:
    user_id: int
    text: str
    keyboard: str

    type: TypeMessage
    event_id: str = None
    peer_id: int = None
    event_data: str = None

    @property
    def as_bytes(self) -> bytes:
        return pickle.dumps(
            {
                "type": self.type.value,
                "user_id": self.user_id,
                "text": self.text,
                "keyboard": self.keyboard,
                "event_id": self.event_id,
                "peer_id": self.peer_id,
                "event_data": self.event_data,
            }
        )
