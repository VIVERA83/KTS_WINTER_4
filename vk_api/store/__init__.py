import typing

from store.database.rabbitmq import RabbitMQ

if typing.TYPE_CHECKING:
    from core.app import Application


class Store:
    def __init__(self, app: "Application"):
        from store.vk_api.accessor import VkApiAccessor

        self.vk_api = VkApiAccessor(app)
        self.rabbitmq = RabbitMQ(app)


def setup_store(app: "Application"):
    app.store = Store(app)
