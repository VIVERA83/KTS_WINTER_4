import os

from pydantic import BaseModel, BaseSettings

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__name__)))


class Postgres(BaseModel):
    db: str
    host: str = "127.0.0.1"
    port: int = 5432
    password: str
    user: str
    db_schema: str = "game"

    @property
    def dsn(self) -> str:
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}"


class Apispec(BaseModel):
    title: str = "Что? Где? Когда?"
    swagger_path: str = "/"


class Settings(BaseSettings):
    postgres: Postgres
    apispec: Apispec

    logging_level: str = "INFO"
    logging_guru: bool = True
    session_key: str = None
    cookie_name: str = "CHAT"
    cookie_expire: int
    host: str = "localhost"
    port: int = 8100

    class Config:
        env_nested_delimiter = "__"
        env_file = BASE_DIR + "/.game_service_env_local"
        enf_file_encoding = "utf-8"
