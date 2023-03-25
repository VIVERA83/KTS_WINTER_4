from dataclasses import dataclass

from game.data_classes import GameSession, Question, Round, User
from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.schema import ForeignKey
from store.database.postgres import GameBase


class UserGameSessionModel(GameBase):
    __tablename__ = "user_game_session"

    user_id: Mapped[int] = Column(
        Integer, ForeignKey("users.id"), primary_key=True, nullable=True
    )
    game_session_id: Mapped[int] = Column(
        Integer, ForeignKey("game_sessions.id"), primary_key=True, nullable=True
    )


class UserModel(GameBase):
    __dataclass__ = User
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    vk_user_id: Mapped[int] = Column(Integer, unique=True)
    username: Mapped[str] = Column(String)

    game_sessions: Mapped[list["GameSessionModel"]] = relationship(
        secondary=UserGameSessionModel.__table__, back_populates="users", lazy="joined"
    )
    rounds: Mapped[list["RoundModel"]] = relationship(lazy="joined")

    @property
    def as_dataclass(self) -> "User":
        return self.__dataclass__(
            id=self.id,
            vk_user_id=self.vk_user_id,
            username=self.vk_user_id,
            game_sessions=[
                game_session.as_dataclass for game_session in self.game_sessions
            ],
            rounds=[round_.as_dataclass for round_ in self.rounds],
        )


class GameSessionModel(GameBase):
    __dataclass__ = GameSession
    __tablename__ = "game_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    captain_id: Mapped[int] = Column(Integer, nullable=False)
    users: Mapped[list["UserModel"]] = relationship(
        secondary=UserGameSessionModel.__table__,
        back_populates="game_sessions",
        lazy="joined",
    )
    rounds: Mapped[list["RoundModel"]] = relationship(lazy="joined")

    @property
    def as_dataclass(self) -> "GameSession":
        return self.__dataclass__(
            id=self.id,
            captain_id=self.captain_id,
            users=[
                User(
                    id=user.id,
                    vk_user_id=user.vk_user_id,
                    username=user.username,
                    game_sessions=[],
                    rounds=[],
                )
                for user in self.users
            ],
            rounds=[round_.as_dataclass for round_ in self.rounds],
        )


class RoundModel(GameBase):
    __dataclass__ = Round
    __tablename__ = "rounds"

    id: Mapped[int] = Column(Integer, primary_key=True)
    answer: Mapped[str] = Column(String, nullable=False)
    round_number: Mapped[int] = Column(
        Integer,
        nullable=False,
    )
    is_correct: Mapped[bool] = Column(Boolean, nullable=False)
    # User держащий ответ
    respondent: Mapped["UserModel"] = relationship(
        back_populates="rounds", uselist=False, lazy="joined"
    )
    respondent_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    game_session_id: Mapped[int] = mapped_column(ForeignKey("game_sessions.id"))

    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"))

    @property
    def as_dataclass(self) -> "Round":
        return self.__dataclass__(
            id=self.id,
            answer=self.answer,
            round_number=self.round_number,
            is_correct=self.is_correct,
            respondent=User(
                    id=self.respondent.id,
                    vk_user_id=self.respondent.vk_user_id,
                    username=self.respondent.username,
                    game_sessions=[],
                    rounds=[],
                ),
            respondent_id=self.respondent_id,
            question_id=self.question_id,
            game_session_id=self.game_session_id,
        )


@dataclass
class QuestionModel(GameBase):
    __dataclass__ = Question
    __tablename__ = "questions"

    id: Mapped[int] = Column(Integer, primary_key=True)
    title: Mapped[str] = Column(String, nullable=False, unique=True)
    correct_answer: Mapped[str] = Column(String, nullable=False)
    rounds: Mapped[list["RoundModel"]] = relationship(lazy="joined")

    @property
    def as_dataclass(self) -> "Question":
        return self.__dataclass__(
            id=self.id,
            title=self.title,
            correct_answer=self.correct_answer,
            rounds=[round_.as_dataclass for round_ in self.rounds],
        )
