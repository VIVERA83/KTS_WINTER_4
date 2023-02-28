from dataclasses import dataclass
from typing import Optional, Type, Union

from marshmallow import EXCLUDE, Schema, fields, post_load, pre_load
from marshmallow_enum import EnumField

from bot.data_classes import MessageFromVK, Payload, MessageToVK, TypeMessage

objects = Union[Type[Payload],]


class BaseSchema(Schema):
    __model__: Optional[dataclass] = None

    @post_load
    def make_object(self, data, **_: dict) -> objects:
        return self.__model__(**data)

    class Meta:
        unknown = EXCLUDE
        ordered = True


class PayloadSchema(BaseSchema):
    __model__ = Payload

    keyboard_name = fields.Str(missing=None)
    button_name = fields.Str(missing=None)


class MessageFromVKSchema(BaseSchema):
    __model__ = MessageFromVK

    user_id = fields.Integer()
    body = fields.String()
    payload = fields.Nested(PayloadSchema())
    type = EnumField(TypeMessage)
    event_id = fields.Str(missing=None)
    peer_id = fields.Int(missing=None)
    event_data = fields.Str(missing=None)

    @pre_load
    def make(self, data, **_: dict) -> objects:
        if not data.get("body"):
            data["body"] = data["payload"]["button_name"]
        return data


class MessageToVKSchema(BaseSchema):
    __model__ = MessageToVK

    user_id = fields.Integer()
    text = fields.String()
    keyboard = fields.Str()

    event_id = fields.Str(missing=None)
    peer_id = fields.Int(missing=None)
    type = EnumField(TypeMessage)
    event_data = fields.Str(missing=None)
