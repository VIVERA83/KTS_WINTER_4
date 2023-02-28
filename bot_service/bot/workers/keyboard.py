import logging
from asyncio import CancelledError, Queue, Task
from time import monotonic
from typing import TYPE_CHECKING, Callable, Optional

from bot.data_classes import MessageFromVK, MessageToVK

from ..vk.vk_keyboard.keyboard import Keyboard
from .poller import BasePoller

if TYPE_CHECKING:
    from dispatcher import Bot
    from user import User


class Keyboard(BasePoller):
    # штука генерирует клавиатуру для VK
    keyboard: Optional[Keyboard] = None
    # Действия забитые на кнопки
    button_handler: Optional[dict[str, Callable]] = {}
    # Действия забитые на определенный входящий текст
    text_handler: Optional[dict[Optional[str], Callable]] = {}

    def __init__(
            self,
            bot: "Bot",
            name: str,
            timeout: int,
            user_timeout: int = None,
            is_dynamic: bool = False,
            logger: Optional[logging.Logger] = None,
    ):
        self.bot = bot
        self.name = name
        # входящие сообщения от "User", VK
        self.queue_input = Queue()
        # время существования клавиатуры
        self.timeout = timeout
        # время ожидания ответа от пользователя, None - ограничений нет, све время жизни клавиатуры
        self.user_timeout = user_timeout
        self.current_user: Optional["User"] = None
        # список пользователей
        self.users: Optional[list[int]] = []
        # объекты (другие клавиатуры) за изменением которых наблюдаем
        self.tracked_objects: Optional[list] = []
        #
        self.expired: Optional[float] = 0
        self.is_running = False
        # Обновление клавиатуры отправлять всем или только новым
        self.is_dynamic = is_dynamic
        self.worker_task: Optional[Task] = None
        self.check_expired_task: Optional[Task] = None
        self.logger = logger or logging.getLogger(self.name)

    async def send_message_to_up(self, message: MessageToVK):
        user = self.bot.get_user_by_id(message.user_id)
        await user.send_message_to_up(message)

    async def send_message_to_up_for_all(self, message: MessageToVK):
        for user_id in self.users:
            message.user_id = user_id
            await self.send_message_to_up(message)

    def add_user(self, user_id: int) -> "User":
        """
        Добавляем User в список, кому приходят обновление по клавиатуре
        """
        if user_id not in self.users:
            self.users.append(user_id)
        return self.get_user(user_id)

    def get_user(self, user_id: int) -> "User":
        """
        Получаем пользователя, который находится в текущей клавиатуре
        """
        if user_id in self.users:
            if user := self.bot.get_user_by_id(user_id):
                return user
            else:
                raise KeyError(f"User with id {user_id} not found")

    def delete_user(self, user_id: int):
        for index, id_ in enumerate(self.users.copy()):
            if user_id == id_:
                self.users.pop(index)

    async def inbound_message_handler(self):
        while self.is_running:
            try:
                message = await self.queue_input.get()
                # обновляем срок действия
                self.expired = monotonic()
                # добавляем нового пользователя, которые находятся в меню
                user = self.add_user(message.user_id)
                # Задаем пользователю новое текущие место положения
                user.current_keyboard = self.name
                # выявляем нажатие на кнопку
                if handler := self.button_handler.get(
                        message.payload.button_name, None
                ):
                    # исполняем нажатие на кнопку
                    await handler(self.bot, message)
                else:
                    # обрабатываем событие из body - text что пришел от пользователя
                    await self.text_handlers(message)
                    if handler := self.text_handler.get(message.body, None):
                        await handler(self.bot, message)
                    message_to_vk = self.create_message_to_vk(message)
                    # если действия пользователя должны отражаться для всех участников Keyboard
                    if self.is_dynamic:
                        await self.send_message_to_up_for_all(message_to_vk)
                    else:
                        await self.send_message_to_up(message_to_vk)
            except CancelledError:
                break
        self.bot.delete_keyboard(self.name)

    async def text_handlers(self, message: MessageFromVK):
        # вызывает обработчик на входящею строку, или обработчик на все сообщения, если он описан
        handler = self.text_handler.get(message.body, None) or self.text_handler.get(
            None, None
        )
        if handler:
            await handler(self.bot, message)

    def create_message_to_vk(self, message: MessageFromVK) -> MessageToVK:
        """Генерация сообщения для VK"""
        message_to_vk = MessageToVK(
            user_id=message.user_id,
            text=message.body,
            keyboard=self.keyboard.as_str,
            type=message.type,
            event_id=message.event_id,
            peer_id=message.peer_id,
            event_data=message.event_data or message.payload.button_name,
        )
        return message_to_vk
