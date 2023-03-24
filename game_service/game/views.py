import json
from random import randint, choice

from aiohttp.web_exceptions import HTTPException, HTTPUnprocessableEntity
from aiohttp_apispec import docs, request_schema, response_schema, querystring_schema
from sqlalchemy.exc import NoResultFound

from core.componets import View
from core.utils import json_response, error_json_response
from game.data_classes import RoundData
from game.models import UserModel
from game.schemas import (
    GameSessionRequestSchema,
    QuestionRequestSchema,
    QuestionSchema,
    UserIdRequestSchema,
    UserRequestSchema,
    UserSchema,
    GameSessionSchema,
    RoundRequestSchema,
    RoundSchema,
)
from icecream import ic


class UserAddView(View):
    @docs(
        tags=["post", "user"],
        summary="Добавить нового игрока",
        description="Добавление игрока в игру ```Что? Где? Когда?```\n"
                    "Обратите внимание что ```vk_user_id``` не должен повторяться\n"
                    "Желательно заполнить ```username```",
    )
    @request_schema(UserRequestSchema)
    @response_schema(UserSchema)
    async def post(self):
        user = await self.store.game.add_user(self.data)
        self.logger.debug(f"{self.__class__.__name__} : {user}")
        return json_response(data=UserSchema().dump(user.as_dataclass))


class UserGetByIdViews(View):
    @docs(
        tags=[
            "user",
            "get",
        ],
        summary="Получить игрока по id",
        description="Получить данные по игроку ```Что? Где? Когда?```\n",
    )
    @querystring_schema(UserIdRequestSchema)
    @response_schema(UserSchema)
    async def get(self):
        user = await self.store.game.get_user_by_id(self.data.id)
        self.logger.debug(f"{self.__class__.__name__} : {user}")
        return json_response(
            data=UserSchema().dump(user.as_dataclass if user else None)
        )


class UserGetByVkIdViews(View):
    @docs(
        tags=[
            "user",
            "get",
        ],
        summary="Получить игрока по vk_id",
        description="Получить данные по игроку ```Что? Где? Когда?```\n",
    )
    @querystring_schema(UserIdRequestSchema)
    @response_schema(UserSchema)
    async def get(self):
        user = await self.store.game.get_user_by_vk_id(self.data.id)
        self.logger.debug(f"{self.__class__.__name__} : {user}")
        return json_response(
            data=UserSchema().dump(user.as_dataclass if user else None)
        )


#  Questions
class QuestionAddView(View):
    @docs(
        tags=["post"],
        summary="Добавить новый вопрос",
        description="Добавление вопроса в игру ```Что? Где? Когда?```\n"
                    "Обратите внимание что вопрос не должен повторяться\n"
                    "Ответ на вопрос желательно должен быть одним словом",
    )
    @request_schema(QuestionRequestSchema)
    @response_schema(QuestionSchema)
    async def post(self):
        question = await self.store.game.add_question(self.data)
        self.logger.debug(f"{self.__class__.__name__} : {question}")
        return json_response(data=QuestionSchema().dump(question.as_dataclass))


# GameSession
class GameSessionAddViews(View):
    @docs(
        tags=["post"],
        summary="Добавить игровую сессию",
        description="Добавление игровой сессии в игру ```Что? Где? Когда?```\n"
                    "```captain_id``` - капитан команды, ```vk_user_id```\n"
                    "```users``` - список игроков, ```vk_user_id```\n",
    )
    @request_schema(GameSessionRequestSchema)
    @response_schema(GameSessionSchema)
    async def post(self):
        self.data.users = await self.gather_users()
        game_session = await self.store.game.add_game_session(self.data)
        self.logger.debug(f"{self.__class__.__name__} : {game_session}")
        return json_response(data=GameSessionSchema().dump(game_session.as_dataclass))

    async def gather_users(self) -> list["UserModel"]:
        """Собираем пользователей, тех что нет в базе создаем, те что есть вытаскиваем из бд"""
        users = []
        for vk_user_id in self.data.users:
            user = await self.store.game.get_user_by_vk_id(vk_user_id)
            if not user:
                # TODO: добавить поход в вк за именем пользователя
                user = await self.store.game.add_user(
                    UserRequestSchema().load({"vk_user_id": vk_user_id})
                )
            users.append(user)
        return users


class QuestionGetView(View):
    @docs(
        tags=["get", ],
        summary="Получить список вопросов ",
        description="Получить список вопросов ```Что? Где? Когда?```", )
    @response_schema(QuestionSchema)
    async def get(self):
        questions = await self.store.game.list_questions()
        ic(questions)
        self.logger.debug(f"{self.__class__.__name__} : {len(questions)}")
        return json_response(data=QuestionSchema(many=True).dump(questions if questions else None))


# Не оптимальный вариант переделай
class QuestionGeRandomView(View):
    @docs(
        tags=["get", ],
        summary="Получить случайный вопрос ",
        description="Получить случайный вопрос ```Что? Где? Когда?```", )
    @response_schema(QuestionSchema)
    async def get(self):
        questions = await self.store.game.list_questions()
        question = choice(questions)
        self.logger.debug(f"{self.__class__.__name__} : {len(questions)}")
        return json_response(data=QuestionSchema().dump(question))


# Round
class RoundAddViews(View):
    @docs(
        tags=[
            "post",
        ],
        summary="Сохранить итоги раунда",
        description="Сохранить итоги раунда в игровой сессии ```Что? Где? Когда?```\n",
    )
    @request_schema(RoundRequestSchema)
    @response_schema(RoundSchema)
    async def post(self):
        round_number = await self.store.game.get_count_rounds(self.data.game_session_id) + 1
        try:
            is_correct = (await self.store.game.get_correct_answer(self.data.question_id)) == self.data.answer
        except NoResultFound:
            raise HTTPUnprocessableEntity(reason=f"The question with this id ({self.data.question_id}) not found",
                                          text=json.dumps(self.data.as_dict))
        round_data = RoundData(**self.data.as_dict, **{"round_number": round_number, "is_correct": is_correct})
        round_game = await self.store.game.add_round(round_data)
        self.logger.debug(f"{self.__class__.__name__} : {round_game}")
        return json_response(data=RoundSchema().dump(round_game.as_dataclass))
