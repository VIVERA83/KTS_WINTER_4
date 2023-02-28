import logging
from asyncio import CancelledError, Queue, Task, create_task, sleep
from time import monotonic
from typing import Optional

from bot.data_classes import MessageFromVK, MessageToVK


class BasePoller:
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
        self.inbound_message_worker.cancel()
        self.outbound_message_worker.cancel()
        await self.inbound_message_worker
        await self.outbound_message_worker
        await self.check_expired_task
        self.logger.info(f"{self.__repr__()} is stopping")

    async def poller_expired(self):
        """Закрывает workers по достижению timeout"""
        if not self.timeout:
            self.is_unlimited = True
        while self.is_running:
            try:
                if self.is_unlimited:
                    await sleep(2)
                else:
                    await sleep((self.expired + self.timeout) - monotonic())
                    if (self.expired + self.timeout) < monotonic():
                        self.is_running = False
                        self.inbound_message_worker.cancel()

            except CancelledError:
                self.is_running = False

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

    async def send_message_to_down(self, message: MessageFromVK):
        """
        Добавление в очередь сообщения на отправку вниз по иерархической ветке
        эти сообщения попадают в конченом счете в inbound_message_handler
        """
        await self.queue_input.put(message)

    def __repr__(self):
        return f"{self.__class__.__name__} (name={repr(self.name)})"
