import typing

from store.database.postgres import GameDatabase
from store.game.game_accessor import GameAccessor

if typing.TYPE_CHECKING:
    from core.app import Application


class Store:
    def __init__(self, app: "Application"):
        self.game = GameAccessor(app)


def setup_store(app: "Application"):
    app.postgres = GameDatabase(app)
    app.store = Store(app)
