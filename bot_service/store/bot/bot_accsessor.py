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
        app.bot = Bot(
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
            finally:
                await message.ack()

        self.is_running = True
        self.session = ClientSession(connector=TCPConnector(verify_ssl=False))
        self.poller = asyncio.create_task(self.send_message())
        self.app.bot.get_user_name = self.get_user_name_by_vk_id
        await app.rabbitmq.create_queue("vk_api_input", on_input_queue)
        await self.app.bot.start()

    async def disconnect(self, app: "Application"):
        await self.app.bot.stop()
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
