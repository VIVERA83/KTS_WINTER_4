import logging
from asyncio import CancelledError, Queue
from typing import Optional, Type, TYPE_CHECKING

from icecream import ic

from bot.data_classes import MessageFromVK, MessageToVK, MessageFromKeyboard
from .keyboard import Keyboard
from .poller import BasePoller
from .user import User

if TYPE_CHECKING:
    from core.componets import Application


class Bot(BasePoller):
    def __init__(
        self,
        app: "Application",
        name: str,
        user_expired: int,  # время существования пользователя, пока он бездействует
        keyboard_expired: int,  # время существования клавиатуру, пока в ней не происходят события
        root_keyboard: Type[
            Keyboard
        ],  # Начальная клавиатура, точка входа для всех пользователей
        queue_input: Queue[MessageFromVK] = Queue(),
        queue_output: Queue[MessageToVK] = Queue(),
        logger: Optional[logging.Logger] = None,
    ):
        self.app = app
        self.name = name
        self.is_running = False
        # Очередь в которой лежат сообщения от VK
        self.queue_input = queue_input
        # Очередь в которой лежат исходящие сообщения для VK
        self.queue_output = queue_output

        # время жизни пользователя без активных действий
        self.user_expired = user_expired
        # время жизни клавиатуры без активных действий
        self.keyboard_expired = keyboard_expired

        # Подключённые User, key = user_id из VK
        self._users: Optional[dict[int, User]] = {}
        # Активные клавиатуры
        self._keyboards: Optional[dict[str, Keyboard]] = {}
        # Начальная клавиатура, стартовая позиция, а так же куда переносить если запрашиваемой

        self.root_keyboard = root_keyboard
        self.logger = logger or logging.getLogger(self.name)

    async def create_user(self, user_id: int) -> User:
        """
        Добавляем пользователя в словарик активных пользователей и запускаем его
        """
        user = User(
            bot=self,
            user_id=user_id,
            user_name=await self.get_user_name(user_id),
            timeout=self.user_expired,
            logger=self.logger,
        )
        await user.start()
        self._users[user_id] = user
        return user

    async def delete_user(self, user_id: int):
        """
        Удаление пользователя
        """
        if user := self._users.pop(user_id, None):
            await user.stop()
            self.logger.debug(f"{self.name} delete user {user_id}")
        else:
            self.logger.error(f"{self.name}: User not found : {user_id}")

    def get_user_by_id(self, user_id) -> User:
        """
        Получить User из словарика активных пользователей
        """
        return self._users.get(user_id, None)

    async def create_keyboard(
        self,
        keyboard_name: str,
        keyboard: Type[Keyboard],
        keyboard_timeout: int,
        user_timeout: int,
        is_dynamic: bool,
    ) -> Keyboard:
        """
        Создаётся клавиатуру и добавляется в словарик активных клавиатур.
        :param keyboard_name:
        :param keyboard:
        :param keyboard_timeout:
        :param user_timeout:
        :param is_dynamic:
        :return:
        """
        keyboard = keyboard(
            bot=self,
            name=keyboard_name,
            timeout=keyboard_timeout,
            user_timeout=user_timeout,
            is_dynamic=is_dynamic,
            logger=self.logger,
        )
        await keyboard.start()
        self._keyboards[keyboard_name] = keyboard
        return keyboard

    def get_keyboard_by_name(self, name: str) -> Keyboard:
        """
        Получить Keyboard из списка активных клавиатур
        """
        return self._keyboards.get(name, None)

    async def delete_keyboard(self, keyboard_name: str):
        """
        Удаление Keyboard из списка активных клавиатур
        """
        if keyboard := self._keyboards.pop(keyboard_name, None):
            await keyboard.stop()
            self.logger.debug(f"{self.name} delete keyboard {keyboard_name}")
        else:
            self.logger.error(f"{self.name}: keyboard not found : {keyboard_name}")

    async def send_message_to_up(self, message: MessageToVK):
        """
        Отправить сообщение, наверх, в Данном случаи,
        сообщение из очереди полетит за пределы сервиса
        """
        await self.queue_output.put(message)

    async def send_message_to_down(self, message: MessageFromVK):
        """
        Отправка сообщения по иерархии вниз, в данном случаи получатель User,
        который находится ниже на 1 ступень.
        """

        user = self.get_user_by_id(message.user_id)
        await user.send_message_to_down(message)

    async def inbound_message_handler(self):
        """Обрабатывает входящие сообщения, при необходимости генерирует User, Keyboard"""
        try:
            while self.is_running:
                # получаем сообщение
                message = await self.queue_input.get()
                # если сообщение пришло из вк
                if isinstance(message, MessageFromVK):
                    await self.vk_message_handler(message)
                # если сообщение пришло от клавиатуры
                elif isinstance(message, MessageFromKeyboard):
                    await self.keyboard_message_handler(message)
                # если вообще ни понятно что пришло
                else:
                    self.logger.warning(f"Unknown message type: {message}")
        except CancelledError:
            self.logger.info(f"Dispatcher cancelled")

    async def vk_message_handler(self, message: MessageFromVK):
        """Обработка сообщений из VK"""
        # если пользователя нет, создаем пользователя, и добавляем его в свой словарик
        user = self.get_user_by_id(message.user_id) or await self.create_user(
            message.user_id
        )
        # если есть активная текущая клавиатура пользователя получаем ее иначе берем начальную
        keyboard = self.get_keyboard_by_name(
            user.current_keyboard
        ) or await self.create_keyboard(
            keyboard_name=self.root_keyboard.name,
            keyboard=self.root_keyboard,
            keyboard_timeout=self.keyboard_expired,
            user_timeout=self.user_expired,
            is_dynamic=False,
        )
        # записываем название клавиатуры, в которую летит сообщение
        message.payload.keyboard_name = keyboard.name
        # отправляем пользователю сообщение
        await self.send_message_to_down(message)

    async def keyboard_message_handler(self, message: MessageFromKeyboard):
        # если клавиатура есть, отправляем ей сообщение
        if keyboard := self.get_keyboard_by_name(message.keyboard_name):
            await keyboard.send_message_to_down(message)
        else:
            self.logger.error(f"Keyboard not found: {message.keyboard_name}")

    # Переопределенные методы

    async def get_user_name(self, user_id: int) -> str:
        """
        Получаем user.name по id пользователя из VK?
        Данный метод переопределен в bot_accsessor.py в методе connect
        """
        return f"{self.name}, user_id={user_id}"

    # async def create_game_session(self, data: dict):
    #     """
    #         Данный метод переопределен в bot_accsessor.py в методе connect
    #         example:
    #         data = {"captain_id": 1,
    #                 "users": [1, 2, 3,] # VK_user_id
    #                 }
    #         Временный Вариант
    #     """
    #
    # async def get_random_question(self) -> dict:
    #     """
    #         Данный метод переопределен в bot_accsessor.py в методе connect
    #         example:
    #         data = {"id": 41,
    #                 "title": "Сколько будет 2+2х2=?",
    #                 "correct_answer": "6",
    #                 "rounds": []
    #                }
    #         Временный Вариант
    #     """
