import typing

from store.bot.bot_accsessor import BotAccessor
from store.rabbitmq.rabbitmq_accessor import RabbitMQ

if typing.TYPE_CHECKING:
    from core.app import Application


class Store:
    def __init__(self, app: "Application"):
        from store.api_game_www.accessor import WwwApiAccessor

        self.api_game_www = WwwApiAccessor(app)
        self.bot = BotAccessor(app)


def setup_store(app: "Application"):
    app.rabbitmq = RabbitMQ(app)
    app.store = Store(app)
