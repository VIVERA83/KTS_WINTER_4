import typing

from store.database.postgres import PostgresDatabase

if typing.TYPE_CHECKING:
    from core.app import Application


class Store:
    def __init__(self, app: "Application"):
        pass


def setup_store(app: "Application"):
    app.postgres = PostgresDatabase(app)
    app.store = Store(app)
