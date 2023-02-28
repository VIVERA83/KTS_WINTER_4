import logging
from asyncio import Queue
from typing import TYPE_CHECKING, Optional

from bot.data_classes import MessageFromVK, MessageToVK

from .poller import BasePoller

if TYPE_CHECKING:
    from dispatcher import Bot


class User(BasePoller):
    def __init__(
        self,
        bot: "Bot",
        user_id: int,
        user_name: str,
        timeout: int,
        logger: Optional[logging.Logger] = None,
    ):
        self.bot = bot
        self.user_id = user_id
        self.name = user_name
        # время жизни
        self.timeout = timeout
        # точка отсчета
        self.expired: Optional[float] = None
        # Очередь в которой лежат сообщения от VK
        self.queue_input: Queue[MessageFromVK] = Queue()
        # Текущие меню
        self.current_keyboard: Optional[str] = None
        self.is_running = False
        self.logger = logger or logging.getLogger(self.name)

    def empty_queue_input(self):
        """
        Очистка очереди входящих сообщений, пока первое сообщение не обработано и не отправлено
        остальные игнорируются
        """
        while not self.queue_input.empty():
            self.queue_input.get_nowait()
            self.queue_input.task_done()

    async def send_message_to_up(self, message: MessageToVK):
        """Добавление в очередь сообщения на отправку в Bot"""
        await self.bot.send_message_to_up(message)

    async def send_message_to_down(self, message: MessageFromVK):
        """
        Отправка сообщение в клавиатуру
        """
        keyboard = self.bot.get_keyboard_by_name(message.payload.keyboard_name)
        await keyboard.send_message_to_down(message)
