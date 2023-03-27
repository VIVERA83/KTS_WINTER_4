from typing import TYPE_CHECKING, Callable, Optional

from aio_pika import Message, connect
from aio_pika.abc import AbstractChannel, AbstractConnection, AbstractQueue
from base.base_accessor import BaseAccessor

from base.backoff import before_execution

if TYPE_CHECKING:
    from core.app import Application


class RabbitMQ(BaseAccessor):
    _connection: Optional[AbstractConnection] = None
    _channel: Optional[AbstractChannel] = None

    async def connect(self, app: "Application"):
        self._connection = await before_execution(logger=self.logger)(connect)(app.settings.rabbitmq.dns)
        self._channel = await self._connection.channel()
        self.logger.info("Connected to RabbitMQ")

    async def disconnect(self, app: "Application"):
        await self._connection.close()
        self.logger.info("Disconnected from RabbitMQ")

    async def send_message(self, data: bytes, routing_key: str):
        """Отправить сообщение, в rabbit по адресу routing_key"""
        await self.app.rabbitmq._channel.default_exchange.publish(
            message=Message(data), routing_key=routing_key
        )

    # TODO: Придумать адекватное название
    async def create_queue(self, name: str, consumer: Callable) -> AbstractQueue:
        """
        Назначить слушателя сообщений из rabbit по адресу name обработчика consumer
        :param name: Имя ящика в rabbit сообщения из которого будем обрабатывать.
        :param consumer: Функция, которая будет обрабатывать входящие сообщения с ящика.
        :return:
        """
        queue = await self._channel.declare_queue(name)
        await queue.consume(consumer)
        return queue
