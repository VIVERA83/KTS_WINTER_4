import asyncio
from asyncio import Task
from typing import Optional

from store.vk_api.data_classes import MessageFromVK, Payload
from store import Store
from store.vk_api.data_classes import TypeMessage


class Poller:
    def __init__(self, store: Store):
        self.store = store
        self.is_running = False
        self.poll_from_vk_task: Optional[Task] = None

    async def start(self):
        self.is_running = True
        self.poll_from_vk_task = asyncio.create_task(self.poll_from_vk())

    async def stop(self):
        self.is_running = False
        await self.poll_from_vk_task

    async def poll_from_vk(self):
        """
        Читает сообщения из ВК и отправляет их в RabbitMQ
        """
        while self.is_running:
            for update in await self.store.vk_api.poll():
                if update.type.value in [
                    TypeMessage.message_new.value,
                    TypeMessage.message_event.value,
                ]:
                    message = MessageFromVK(
                        user_id=update.object.user_id,
                        body=update.object.body,
                        event_id=update.object.event_id,
                        peer_id=update.object.peer_id,
                        payload=Payload(
                            button_name=update.object.payload.button_name,
                            keyboard_name=update.object.payload.keyboard_name,
                        ),
                        type=update.type,
                    )
                    await self.store.rabbitmq.send(
                        message.as_bytes, self.store.rabbitmq.input_queue_name
                    )
