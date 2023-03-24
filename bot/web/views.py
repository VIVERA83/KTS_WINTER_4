from aiohttp.web_response import json_response
from aiohttp_apispec import docs, querystring_schema, response_schema

from core.componets import View
from web.schemas import IDSchema, UserSchema


class UserNameView(View):
    @docs(
        tags=["Сообщение"],
        summary="Получить имя пользователя",
        description="Получить имя пользователя по `user_id` из VK",
    )
    @querystring_schema(IDSchema)
    @response_schema(UserSchema)
    async def get(self):
        data = await self.bot.get_user_name(self.data.get("id"))
        return json_response(data=data)
