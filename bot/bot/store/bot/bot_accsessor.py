import asyncio
import pickle
from asyncio import CancelledError, Queue, Task
from typing import TYPE_CHECKING, Optional

from aio_pika import IncomingMessage
from aiohttp import ClientSession, TCPConnector, ClientConnectorError

from base.base_accessor import BaseAccessor

from bot.data_classes import MessageFromVK, MessageToVK
from bot.schemes import MessageFromVKSchema
from bot.vk.keyboards.root import RootKeyboard
from bot.workers.dispatcher import Bot

if TYPE_CHECKING:
    from core.componets import Application


class BotAccessor(BaseAccessor):
    session: Optional[ClientSession] = None

    def __init__(self, app: "Application", *args, **kwargs):
        super().__init__(app, *args, **kwargs)
        self._init_()
        self.bot = Bot(
            app=app,
            user_expired=app.settings.bot.user_expired,
            keyboard_expired=app.settings.bot.keyboard_expired,
            root_keyboard=RootKeyboard,
            name=app.settings.bot.name,
            queue_input=self.queue_input,
            queue_output=self.queue_output,
            logger=app.logger,
        )
        self.is_running = False
        self.poller: Optional[Task] = None

    def _init_(self):
        self.queue_input: Optional[Queue[MessageFromVK]] = Queue()
        self.queue_output: Optional[Queue[MessageToVK]] = Queue()
        self.url = self.app.settings.vk_service.url

    async def connect(self, app: "Application"):
        async def on_input_queue(message: IncomingMessage):
            try:
                data = pickle.loads(message.body)
                message_from_vk = MessageFromVKSchema().load(data)
                await self.queue_input.put(message_from_vk)
            except pickle.UnpicklingError as e:
                self.logger.error(f"{e.__class__.__name__} : {e} : {message.body=}")
            # TODO: Может убрать и перенести выше ?
            finally:
                await message.ack()

        self.is_running = True
        self.session = ClientSession(connector=TCPConnector(verify_ssl=False))
        self.poller = asyncio.create_task(self.send_message())
        # Переопределяем методы в Боте
        self.override_bot_methods()
        await app.rabbitmq.create_queue("vk_api_input", on_input_queue)
        await self.bot.start()

    async def disconnect(self, app: "Application"):
        await self.bot.stop()
        await self.session.close()

    async def send_message(self):
        while self.is_running:
            try:
                message = await self.queue_output.get()
            except CancelledError:
                self.is_running = False
                continue
            try:
                await self.app.rabbitmq.send_message(message.as_bytes, "vk_api_output")
            except CancelledError:
                self.is_running = False
        self.logger.info("Sending message to RabbitMQ is stopped")

    async def get_user_name_by_vk_id(self, user_id: int) -> str:
        try:
            async with self.session.get(
                self.url + f"/get_user_name?id={user_id}"
            ) as resp:
                if resp.status != 200:
                    self.logger.error(f"{resp.url} {resp.reason} ")
                return (await resp.json()).get("username")
        except ClientConnectorError as e:
            self.logger.error(e.os_error)

    def override_bot_methods(self):
        """Переопределяем методы бота, бля более быстрого доступа к внешним api"""
        self.bot.get_user_name = self.get_user_name_by_vk_id
        # self.app.bot.create_game_session = self.create_game_session
        # self.app.bot.get_random_question = self.get_random_question

    # async def create_game_session(self, data: dict):
    #     """Временный вариант создание игровой сессии """
    #
    #     url = "http://0.0.0.0:8100/add_game_session"
    #     for user_id in data["users"]:
    #         await self.create_user(user_id)
    #     async with self.session.post(url, data=data) as resp:
    #         return (await resp.json()).get("data")
    #
    # async def create_user(self, user_id: int):
    #     """Временный вариант создание нового пользователя """
    #
    #     url = "http://0.0.0.0:8100/add_user"
    #     data = {
    #         "vk_user_id": user_id,
    #         "username": await self.get_user_name_by_vk_id(user_id)
    #     }
    #     async with self.session.post(f"{url}", data=data) as resp:
    #         ic(await resp.json())
    #
    # async def get_random_question(self):
    #     url = "http://0.0.0.0:8100/get_random_question"
    #     async with self.session.get(url=url) as resp:
    #         return ic(await resp.json()).get("data")

    async def set_keyboard_timeout(self, timeout: int):
        self.app.bot.keyboard_expired = timeout
