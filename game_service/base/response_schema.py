from marshmallow import Schema, fields


class ResponseOkSchema(Schema):
    status_code = fields.Int(default=200)
    status = fields.String(default="OK")
    message = fields.String(default="Success")

    class Meta:
        ordered = True


class ResponseErrorSchema(Schema):
    status = fields.String()
    message = fields.String()
    data = fields.Dict(default={})

    class Meta:
        ordered = True
