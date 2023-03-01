import json
from typing import Any, Optional, TYPE_CHECKING
from aiohttp.web import json_response as aiohttp_json_response
from aiohttp.web_response import Response
from sqlalchemy.exc import IntegrityError
from aiohttp.web_exceptions import HTTPUnprocessableEntity, HTTPException

if TYPE_CHECKING:
    from core.componets import Request


def json_response(data: Any = None, status: str = "ok") -> Response:
    if data is None:
        data = {}
    return aiohttp_json_response(
        data={
            "status": status,
            "data": data,
        }
    )


def error_json_response(
    http_status: int,
    status: str = "error",
    message: Optional[str] = None,
    data: Optional[dict] = None,
):
    if data is None:
        data = {}
    return aiohttp_json_response(
        status=http_status,
        data={
            "status": status,
            "message": str(message),
            "data": data,
        },
    )


async def error_handler(error: Exception, request: "Request", handler):
    if isinstance(error, IntegrityError):
        return error_json_response(
            http_status=HTTPUnprocessableEntity.status_code,
            message=HTTPUnprocessableEntity().reason,
            data=handler_integrity_error(error),
        )
    # Наступает если запрос пришел с ошибкой от клиента, до views
    if isinstance(error, HTTPUnprocessableEntity):
        return error_json_response(
            http_status=error.status_code,
            message=error.reason,
            data=json.loads(error.body),
        )
    if isinstance(error, HTTPException):
        # Наступает если ошибка инициализирована где-то во views
        return error_json_response(
            http_status=error.status_code,
            status=error.reason,
            message=error.text,
        )
    # Возможно наступление если где-то во views будет происходить ошибка при исполнении кода
    request.app.logger.error(
        f"Exception {str(error.args)}",
    )
    return error_json_response(
        http_status=500,
        message="Internal Server Error",
    )


def handler_integrity_error(error) -> dict:
    word_0, _, word_2 = error.args[0].partition("=")
    _, _, key = word_0.partition("Key")
    key = key[2:-1]
    value = word_2.partition(")")[0][1:]
    return {
        key: [
            f"The parameter with the value `{value}` does not meet the uniqueness condition"
        ]
    }
