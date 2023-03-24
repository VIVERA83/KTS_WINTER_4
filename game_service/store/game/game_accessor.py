"""Модуль описывающий обращения к базе данных"""
from base.base_accessor import BaseAccessor
from game.data_classes import (
    GameSessionRequest,
    Question,
    QuestionRequest,
    UserRequest,
    User,
    GameSession,
    Round, RoundData,
)
from game.models import (
    GameSessionModel,
    QuestionModel,
    UserGameSessionModel,
    UserModel,
    RoundModel,
)
from icecream import ic
from sqlalchemy import ChunkedIteratorResult, CursorResult, insert, select, func
from sqlalchemy.orm import selectinload


class GameAccessor(BaseAccessor):
    async def add_question(self, question: QuestionRequest) -> QuestionModel:
        async with self.app.postgres.session.begin().session as session:
            async with session:
                query = (
                    insert(QuestionModel)
                    .values(**question.as_dict)
                    .options(selectinload(QuestionModel.rounds))
                    .returning(QuestionModel)
                )
                result: ChunkedIteratorResult = await session.execute(query)  # noqa
        return result.scalars().first()

    async def list_questions(self) -> list[Question]:
        async with self.app.postgres.session.begin().session as session:
            async with session:
                result = await session.execute(
                    select(QuestionModel.id, QuestionModel.title, QuestionModel.correct_answer))
            return [Question(*question, rounds=[]) for question in result.all()]


    async def add_user(self, user: UserRequest) -> UserModel:
        async with self.app.postgres.session.begin().session as session:
            async with session:
                query = (
                    insert(UserModel)
                    .values(**user.as_dict)
                    .options(
                        selectinload(UserModel.game_sessions),
                        selectinload(UserModel.rounds),
                    )
                    .returning(UserModel)
                )
                result: CursorResult = await session.execute(query)  # noqa
                await session.commit()
        return result.unique().scalars().first()

    async def add_game_session(self, game_session: GameSession) -> GameSessionModel:
        async with self.app.postgres.session.begin().session as session:
            async with session.begin():
                # создаем игровую сессию
                game_session_model = GameSessionModel(
                    **{"captain_id": game_session.captain_id}
                )
                session.add(game_session_model)
            async with session.begin():
                session.add_all(
                    [
                        UserGameSessionModel(
                            **{
                                "user_id": user.id,
                                "game_session_id": game_session_model.id,
                            }
                        )
                        for user in game_session.users
                    ]
                )

            stmt = (
                select(GameSessionModel)
                .join(UserGameSessionModel)
                .options(
                    selectinload(GameSessionModel.users),
                    selectinload(GameSessionModel.rounds),
                )
                .where(GameSessionModel.id == game_session_model.id)
            )
            result = await session.execute(stmt)

        return result.unique().scalars().first()

    async def add_round(self, data: RoundData) -> RoundModel:
        async with self.app.postgres.session.begin().session as session:
            async with session.begin():
                query = (
                    insert(RoundModel)
                    .values(**data.as_dict)
                    .options(
                        selectinload(RoundModel.respondent))
                    .returning(RoundModel)
                )
                result: CursorResult = await session.execute(query)  # noqa
            return result.unique().scalars().first()

    async def get_game_result(self, game_session_id: int):
        return "get_game_result"

    async def get_game_session_by_id(self, game_session_id: int) -> GameSessionModel:
        async with self.app.postgres.session.begin() as session:
            query = select(UserModel.game_sessions).options(
                selectinload(UserModel.game_sessions)
            )

            result: ChunkedIteratorResult = await session.execute(query)  # noqa
            ses = result.scalars().first()
            return ses

    async def get_user_by_id(self, user_id: int) -> UserModel:
        async with self.app.postgres.session.begin().session as session:
            async with session:
                query = (
                    select(UserModel)
                    .filter(UserModel.id == user_id)
                    .options(
                        selectinload(UserModel.game_sessions),
                        selectinload(UserModel.rounds),
                    )
                )
                result = await session.execute(query)  # noqa
        return result.unique().scalars().first()

    async def get_user_by_vk_id(self, vk_user_id: int) -> UserModel:
        async with self.app.postgres.session.begin().session as session:
            async with session:
                query = (
                    select(UserModel)
                    .filter(UserModel.vk_user_id == vk_user_id)
                    .options(
                        selectinload(UserModel.game_sessions),
                        selectinload(UserModel.rounds),
                    )
                )
                result = await session.execute(query)  # noqa
        return result.unique().scalars().first()

    # TODO: добавить View
    async def get_count_rounds(self, game_session_id: int) -> int:
        async with self.app.postgres.session.begin().session as session:
            async with session:
                smtp = (
                    select(func.count())
                    .select_from(RoundModel)
                    .where(RoundModel.game_session_id == game_session_id)
                )
            return (await session.execute(smtp)).scalar_one()

    # TODO: добавить View
    async def get_correct_answer(self, question_id: int) -> int:
        async with self.app.postgres.session.begin().session as session:
            async with session:
                smtp = (
                    select(QuestionModel.correct_answer)
                    .where(QuestionModel.id == question_id)
                )
            return (await session.execute(smtp)).scalar_one()
