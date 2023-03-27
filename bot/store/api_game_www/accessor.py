from typing import Optional, TYPE_CHECKING
from aiohttp import ClientSession, TCPConnector

from api_game_www.data_classes import GameSessionRequest, UserRequest, Question, RoundRequest
from base.base_accessor import BaseAccessor

if TYPE_CHECKING:
    from core.app import Application


class WwwApiAccessor(BaseAccessor):
    def __init__(self, app: "Application", *args, **kwargs):
        super().__init__(app=app, *args, **kwargs)
        self.session: Optional[ClientSession] = None
        self.url = self.app.settings.game_service.url

    async def connect(self, app: "Application"):
        self.session = ClientSession(connector=TCPConnector(verify_ssl=False))
        self.logger.info(f"{self.__class__.__name__} connect is ready")

    async def disconnect(self, app: "Application"):
        if self.session and not self.session.closed:
            await self.session.close()
        self.logger.info(f"{self.__class__.__name__} connect is closed")

    async def create_game_session(self, game_session: GameSessionRequest):
        """Создание игровой сессии"""
        method = "add_game_session"
        async with self.session.post(
                self.url + method, data=game_session.as_dict
        ) as resp:
            return (await resp.json()).get("data")

    async def create_user(self, user: UserRequest):
        """Создание нового пользователя"""
        method = "add_user"
        async with self.session.post(self.url + method, data=user.as_dict) as resp:
            self.logger.debug(f"{self.__class__.__name__} create_user: {resp.status}")

    async def get_random_question(self) -> Optional["Question"]:
        method = "get_random_question"
        async with self.session.get(self.url + method) as resp:
            if resp.status == 200:
                question_data = (await resp.json()).get("data")
                return Question(**question_data)

    async def save_round_result(self, round_result: "RoundRequest"):
        method = "add_game_round"
        async with self.session.post(self.url + method, data=round_result.as_dict) as resp:
            self.logger.debug(f"{self.__class__.__name__} save_round_result: {resp.status}")
