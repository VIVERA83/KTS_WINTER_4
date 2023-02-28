import pickle
from typing import Optional

from aio_pika import IncomingMessage, Message, connect
from aio_pika.abc import AbstractChannel, AbstractConnection, AbstractQueue
from aio_pika.pool import Pool
from base.base_accessor import BaseAccessor
from store.vk_api.data_classes import EventMessage, MessageToVK, TypeMessage
from store.vk_api.schemes import MessageToVKSchema


class RabbitMQ(BaseAccessor):
    _connection_pool: Optional[Pool] = None
    _connection: Optional[AbstractConnection] = None
    _channel: Optional[AbstractChannel] = None
    input_queue: Optional[AbstractQueue] = None
    output_queue: Optional[AbstractQueue] = None
    input_queue_name = "vk_api_input"
    output_queue_name = "vk_api_output"

    async def connect(self, *_: list, **__: dict):
        self._connection = await connect(self.app.settings.rabbitmq.dns)
        self._channel = await self._connection.channel()
        self.output_queue = await self._channel.declare_queue(self.output_queue_name)
        self.input_queue = await self._channel.declare_queue(self.input_queue_name)
        self.logger.info("Connected to RabbitMQ")

        async def on_output_queue(message: IncomingMessage):
            try:
                data = pickle.loads(message.body)
                message_to_vk: MessageToVK = MessageToVKSchema().load(data)
                # ic(message_to_vk)
                if message_to_vk.type.value == TypeMessage.message_new.value:
                    await self.app.store.vk_api.send_message(message_to_vk)
                elif message_to_vk.type.value == TypeMessage.message_event.value:
                    await self.app.store.vk_api.send_message_event_answer(message_to_vk)
                else:
                    raise TypeError("Unknown message type")
            except pickle.UnpicklingError as e:
                self.logger.error(f"{e.__class__.__name__} : {e} : {message.body=}")
            finally:
                await message.ack()

        await self.output_queue.consume(on_output_queue)

    async def disconnect(self, *_: list, **__: dict):
        await self._connection.close()
        self.logger.info("Disconnected from RabbitMQ")

    async def send(self, data: bytes, routing_key: str):
        await self._channel.default_exchange.publish(
            message=Message(data),
            routing_key=routing_key,
        )
