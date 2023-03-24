import logging
from asyncio import CancelledError, Queue, Task, create_task, sleep
from time import monotonic
from typing import Optional, TYPE_CHECKING, Any, Union

from icecream import ic

from bot.data_classes import MessageFromVK, MessageToVK, MessageFromKeyboard

if TYPE_CHECKING:
    from dispatcher import Bot


class BasePoller:
    bot: Optional["Bot"] = None
    name: Optional[str]
    # входящие сообщение от VK
    queue_input: Optional[Queue[MessageFromVK]] = None
    # исходящие сообщение от VK
    queue_output: Optional[Queue[MessageToVK]] = None
    # Срок жизни
    timeout: Optional[int] = None
    # точка отсчета
    expired: Optional[float] = 0
    is_running: Optional[bool] = False
    # бессмертный
    is_unlimited: Optional[bool] = False
    inbound_message_worker: Optional[Task] = None
    outbound_message_worker: Optional[Task] = None
    check_expired_task: Optional[Task] = None

    logger: Optional[logging.Logger] = None
    # место для хранения каких то данных
    data: Optional[dict[str, Any]] = None
    # объекты (другие клавиатуры, user) которые следят за нами
    tracked_objects: Optional[list[str]] = None
    users: Optional[list[int]] = None

    async def start(self, *_, **__):
        self.is_running = True
        self.expired = monotonic()
        self.inbound_message_worker = create_task(
            self.inbound_message_handler(), name=self.name
        )
        self.outbound_message_worker = create_task(
            self.outbound_message_handler(), name=self.name
        )
        self.check_expired_task = create_task(self.poller_expired())
        self.logger.info(f"{self.__repr__()} is starting")

    async def stop(self, *_, **__):
        self.is_running = False
        self.is_unlimited = False
        self.inbound_message_worker.cancel()
        self.outbound_message_worker.cancel()
        self.check_expired_task.cancel()
        self.logger.info(f"{self.__repr__()} is stopping")

    async def poller_expired(self):
        """Закрывает workers по достижению timeout"""
        if not self.timeout:
            self.is_unlimited = True
        while self.is_running:
            try:
                if self.is_unlimited:
                    await sleep(self.timeout)
                else:
                    await sleep((self.expired + self.timeout) - monotonic())
                    ic(self.expired + self.timeout, monotonic())
                    if (self.expired + self.timeout) < monotonic():
                        self.delete_inactive()
                        if len(self.users) or len(self.tracked_objects):
                            self.expired = monotonic()
                        else:
                            self.is_running = False
                            self.inbound_message_worker.cancel()
                self.expired = monotonic()
            except CancelledError:
                self.is_running = False

    def delete_inactive(self):
        for user_id in self.users.copy():
            if not self.bot.get_user_by_id(user_id):
                try:
                    self.users.remove(user_id)
                except ValueError:
                    self.logger.warning(f"User id not found: {user_id}")

        for keyboard_name in self.tracked_objects.copy():
            if not self.bot.get_keyboard_by_name(keyboard_name):
                try:
                    self.tracked_objects.remove(keyboard_name)
                except ValueError:
                    self.logger.warning(f"Keyboard name not found: {keyboard_name}")

    # нужно обнулить
    async def inbound_message_handler(self):
        """
        Метод обработки входящих сообщений идущих вниз по иерархической ветке,
        необходимо реализовать вечный цикл, с корректным выходом и остановка,
        здесь идет работа с очередью queue_input"""

    # нужно обнулить
    async def outbound_message_handler(self):
        """Метод обработки входящих сообщений идущих наверх по иерархической ветке
        Пример реализации:
        while self.is_running:
            try:
                message = await self.queue_output.get()
                ic(message)
                self.expired = monotonic()
            except CancelledError:
                self.is_running = False
        """

    async def send_message_to_up(self, message: MessageToVK):
        """
        Добавление в очередь сообщения на отправку наверх по иерархической ветке,
        корневой элемент сообщение отправляет во внешний мир (сервис)
        эти сообщения обрабатываются в outbound_message_handler
        """
        await self.queue_output.put(message)

    async def send_message_to_down(
            self, message: Union["MessageFromVK", "MessageFromKeyboard"]
    ):
        """
        Добавление в очередь сообщения на отправку вниз по иерархической ветке
        эти сообщения попадают в конченом счете в inbound_message_handler
        """
        await self.queue_input.put(message)

    def __repr__(self):
        return f"{self.__class__.__name__} (name={repr(self.name)})"
