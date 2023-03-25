import typing

if typing.TYPE_CHECKING:
    from core.app import Application


class BaseAccessor:
    def __init__(self, app: "Application", *_: list, **__: dict):
        self.app = app
        self.logger = app.logger
        app.on_startup.append(self.connect)
        app.on_cleanup.append(self.disconnect)
        self._init_()

    def _init_(self):
        """Описание дополнительных действий для инициализации"""

    async def connect(self, app: "Application"):
        """Логика отвечающая за подключение и настройку модуля к контексту приложения
        как пример настройка подключения к стороннему API
        """

    async def disconnect(self, app: "Application"):
        """Настройка корректного закрытия всех соединений"""
