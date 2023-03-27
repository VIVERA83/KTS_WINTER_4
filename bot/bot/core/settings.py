import os

from pydantic import BaseModel, BaseSettings

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__name__)))


class RabbitMQ(BaseModel):
    user: str
    password: str
    host: str

    @property
    def dns(self) -> str:
        return f"amqp://{self.user}:{self.password}@{self.host}/"


class Bot(BaseModel):
    name: str = "Bot"
    user_expired: int = 100
    keyboard_expired: int = 60


class VKService(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8001

    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}"


class GameService(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8002

    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}/"


class Settings(BaseSettings):
    host: str = "localhost"
    port: int = 8003
    logging_level: str
    logging_guru: bool

    rabbitmq: RabbitMQ
    bot: Bot = Bot()
    vk_service: VKService = VKService()
    game_service: GameService = GameService()

    class Config:
        env_nested_delimiter = "__"
        env_file = BASE_DIR + "/.bot_env_local"
        enf_file_encoding = "utf-8"
