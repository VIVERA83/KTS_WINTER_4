import logging
from asyncio import CancelledError, Queue
from typing import Optional, Type

from bot.data_classes import MessageFromVK, MessageToVK

from .keyboard import Keyboard
from .poller import BasePoller
from .user import User


class Bot(BasePoller):
    def __init__(
        self,
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
        self.name = name
        self.is_running = False
        # Очередь в которой лежат сообщения от VK
        self.queue_input = queue_input
        # Очередь в которой лежат исходящие сообщения для VK
        self.queue_output = queue_output
        # Подключённые User, key = user_id из VK
        self._users: Optional[dict[int, User]] = {}
        # время жизни пользователя без активных действий
        self.user_expired = user_expired
        # время жизни клавиатуры без активных действий
        self.keyboard_expired = keyboard_expired
        # Активные клавиатуры
        self._keyboards: Optional[dict[str, Keyboard]] = {}
        # Начальная клавиатура, стартовая позиция, а так же куда переносить если запрашиваемой
        self.root_keyboard = root_keyboard
        self.logger = logger or logging.getLogger(self.name)

    async def get_user_name(self, user_id: int) -> str:
        """
        Получаем user.name по id пользователя из VK
        """
        return f"{self.name}, user_id={user_id}"

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

    def delete_user(self, user_id: int):
        """
        Удаление пользователя
        """
        self._users.pop(user_id, None)

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
        return self._keyboards.get(name)

    def delete_keyboard(self, keyboard_name: str):
        """
        Удаление Keyboard из списка активных клавиатур
        """
        self._keyboards.pop(keyboard_name, None)

    async def stop_all(self):
        """Остановка всех User и Keyboards"""
        for user in self._users.copy().values():
            if user.is_running:
                await user.stop()

        for keyboard in self._keyboards.copy().values():
            if keyboard.is_running:
                await keyboard.stop()

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
                # записываем название клавиатуры,
                # в которую летит сообщение (при первом обращении  message.payload.keyboard_name = None)
                message.payload.keyboard_name = keyboard.name
                # отправляем пользователю сообщение
                await self.send_message_to_down(message)
        except CancelledError:
            await self.stop_all()
