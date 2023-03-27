import logging
from asyncio import Queue, Task, create_task
from time import monotonic
from typing import Optional, TYPE_CHECKING

from bot.data_classes import MessageFromVK, MessageToVK

if TYPE_CHECKING:
    from dispatcher import Bot


class BasePoller:
    name: Optional[str] = None
    # Основное приложение
    bot: Optional["Bot"] = None
    # логирование, возможно использовать базовый и `logguru`
    logger: Optional[logging.Logger] = None

    # Очереди
    # входящие сообщение от VK
    queue_input: Optional[Queue[MessageFromVK]] = None
    # исходящие сообщение от VK
    queue_output: Optional[Queue[MessageToVK]] = None

    # Срок жизни объекта, таймаут перед проверкой на возможность продления существования объекта
    timeout: Optional[int] = None
    # точка отсчета
    expired: Optional[float] = None
    # Признак работы
    is_running: Optional[bool] = False
    # Признак бессмертный, работает пока не вызовется exception Canceled
    is_unlimited: Optional[bool] = False

    # Workers
    # Задача (worker) который отвечает за обработку входящих сообщений
    inbound_message_worker: Optional[Task] = None
    # Задача (worker) который отвечает за обработку отправку исходящих сообщений
    outbound_message_worker: Optional[Task] = None
    # Задача (worker) который отвечает за время жизни объекта
    check_expired_task: Optional[Task] = None

    async def start(self, *_, **__):
        self.is_running = True
        self.expired = monotonic()
        self.inbound_message_worker = create_task(self.inbound_message_handler())
        self.outbound_message_worker = create_task(self.outbound_message_handler())
        self.check_expired_task = create_task(self.poller_expired())
        self.logger.info(f"{self.__repr__()} is starting")

    async def stop(self, *_, **__):
        self.inbound_message_worker.cancel()
        self.outbound_message_worker.cancel()
        self.check_expired_task.cancel()
        self.logger.info(f"{self.__repr__()} is stopping")

    async def poller_expired(self):
        """Poller контролирует время жизни объекта, возможно продление жизни и другие операции,
        главное, что бы он умел корректно закрывать по отмене и таймаут
        example:

        async def poller_expired(self):
                while self.is_running:
            try:
                await sleep(self.timeout)
            except CancelledError:
                self.is_running = False
        """

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

    def __repr__(self):
        return f"{self.__class__.__name__} (name={repr(self.name)})"
