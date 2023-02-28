import json
from dataclasses import dataclass
from typing import Optional, Type, Union

from marshmallow import EXCLUDE, Schema, fields, post_load, pre_load
from marshmallow_enum import EnumField

from vk_api_sevice.store.vk_api.data_classes import (
    EventMessage,
    Message,
    MessageFromVK,
    MessageToVK,
    Object,
    Payload,
    TypeMessage,
    Update,
    VKResponse,
)

objects = Union[
    Type[VKResponse],
    Type[Update],
    Type[Update],
    Type[Payload],
    Type[Message],
    Type[EventMessage],
]


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

    keyboard_name = fields.Str()
    button_name = fields.Str()


class ObjectSchema(BaseSchema):
    __model__ = Object

    id = fields.Int()
    user_id = fields.Integer(required=True)
    body = fields.String()
    payload = fields.Nested(PayloadSchema(), load_default=Payload())
    event_id = fields.Str()
    peer_id = fields.Int()

    @pre_load
    def make_obj(self, value: Union[str, dict], **_: dict):
        if isinstance(value.get("payload"), str):
            value["payload"] = json.loads(value.get("payload"))
            if not value["payload"].get("data"):
                value["payload"]["data"] = {}
            return value
        return value


class UpdateSchema(BaseSchema):
    __model__ = Update

    type = EnumField(TypeMessage)
    object = fields.Nested(ObjectSchema())


class VKResponseSchema(BaseSchema):
    __model__ = VKResponse

    ts = fields.Integer()
    failed = fields.Int()
    updates = fields.List(fields.Nested(UpdateSchema()), load_default=None)


class MessageFromVKSchema(BaseSchema):
    __model__ = MessageFromVK

    user_id = fields.Integer()
    body = fields.String()
    payload = fields.Nested(PayloadSchema())
    type = EnumField(TypeMessage)
    event_id = fields.Str(missing=None)
    peer_id = fields.Int(missing=None)
    event_data = fields.Str(missing=None)


class MessageToVKSchema(BaseSchema):
    __model__ = MessageToVK

    user_id = fields.Integer()
    text = fields.String()
    keyboard = fields.Str()

    event_id = fields.Str(missing=None)
    peer_id = fields.Int(missing=None)
    type = EnumField(TypeMessage)
    event_data = fields.Str(missing=None)
