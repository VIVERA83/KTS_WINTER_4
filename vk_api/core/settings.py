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


class VK(BaseModel):
    token: str
    group_id: str


class Settings(BaseSettings):
    host: str = "localhost"
    port: int = 8080
    logging_level: str = "INFO"
    logging_guru: bool = True

    rabbitmq: RabbitMQ
    vk: VK

    class Config:
        env_nested_delimiter = "__"
        env_file = BASE_DIR + "/.vk_api_env_local"
        enf_file_encoding = "utf-8"
