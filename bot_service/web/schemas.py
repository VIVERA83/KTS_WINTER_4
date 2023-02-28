from marshmallow import Schema, fields


class IDSchema(Schema):
    id = fields.Int(required=True)


class UserSchema(Schema):
    username = fields.Str()
