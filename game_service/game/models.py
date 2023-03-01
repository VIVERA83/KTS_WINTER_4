from dataclasses import dataclass
from uuid import uuid4

from sqlalchemy import Column, Integer, String, ForeignKey, Table, UUID, BOOLEAN

from sqlalchemy.orm import relationship, Mapped

from store.database.postgres import db


@dataclass
class UserGameSessionModel(db):
    __tablename__ = "user_game_session"

    user: Mapped[int] = Column(Integer, ForeignKey("users.id"), primary_key=True)
    game_session: Mapped[int] = Column(Integer, ForeignKey("game_sessions.id"), primary_key=True)


@dataclass
class UserModel(db):
    __tablename__ = "users"

    id: Mapped[int] = Column(Integer, primary_key=True)
    vk_user_id: Mapped[int] = Column(Integer, unique=True)
    username: Mapped[str] = Column(String)

    game_sessions: Mapped[list["GameSessionModel"]] = relationship(
        secondary=UserGameSessionModel.__table__,
        back_populates="users")


@dataclass
class GameSessionModel(db):
    __tablename__ = "game_sessions"

    id: Mapped[int] = Column(Integer, primary_key=True)
    captain_id: Mapped[int] = Column(Integer, nullable=False)
    users: Mapped[list["UserModel"]] = relationship(
        secondary=UserGameSessionModel.__table__,
        back_populates="game_sessions",
    )
    rounds: Mapped[list["RoundModel"]] = relationship(
        backref="game_sessions",
        cascade="all, delete",
        passive_deletes=True,
    )


@dataclass
class RoundModel(db):
    __tablename__ = "rounds"

    id: Mapped[int] = Column(Integer, primary_key=True)
    answer: Mapped[str] = Column(String, nullable=False)
    round_number: Mapped[int] = Column(Integer, nullable=False)
    # User держащий ответ
    respondent_id: Mapped[int] = relationship(
        "UserModel", backref="rounds", uselist=False
    )
    # Вопрос
    question_id: Mapped[int] = relationship(
        "QuestionModel", backref="rounds", uselist=False
    )
