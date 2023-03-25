from marshmallow import Schema, fields


class IDSchema(Schema):
    id = fields.Int(required=True)


class UserSchema(Schema):
    username = fields.Str()


class TimeOutSchema(Schema):
    timeout = fields.Str(required=True)
