import logging
from asyncio import CancelledError, Queue, Task
from copy import deepcopy
from random import randint
from typing import TYPE_CHECKING, Callable, Optional, Union, Type
from time import monotonic
from asyncio import sleep

from icecream import ic

from bot.data_classes import (
    MessageFromVK,
    MessageToVK,
    MessageFromKeyboard,
    KeyboardEventEnum,
    TypeMessage,
)
from ..vk.keyboards.data_classes import GameSessionSettings, TeamIsReady, TimeoutKeyboard, Round

from ..vk.vk_keyboard.keyboard import Keyboard
from .poller import BasePoller

if TYPE_CHECKING:
    from dispatcher import Bot
    from user import User


class Keyboard(BasePoller):
    # штука генерирует клавиатуру для VK
    keyboard: Optional[Keyboard] = None
    # Действия забитые на кнопки
    button_handler: Optional[dict[str, Callable]] = {}
    # Действия забитые на определенный входящий текст
    text_handler: Optional[dict[Optional[str], Callable]] = {}
    # действия на события в отслеживаемых клавиатурах
    event_handlers: Optional[dict[Optional[str], Callable]] = {}
    # Входящие сообщения от других клавиатур
    queue_input_keyboard: Union[
        Queue["MessageFromKeyboard", "MessageFromKeyboard"]
    ] = None
    # клавиатура в которую переходят все участники после исхода timeout клавиатуры
    timeout_keyboard: Optional["TimeoutKeyboard"] = None

    def __init__(
            self,
            bot: "Bot",
            name: str,
            timeout: int,
            user_timeout: int = None,
            is_dynamic: bool = False,
            logger: Optional[logging.Logger] = None,
            timeout_keyboard: Optional["TimeoutKeyboard"] = None
    ):
        self.bot = bot
        self.name = name
        # входящие сообщения от "User", VK
        self.queue_input = Queue()
        # Входящие сообщения от других клавиатур
        self.queue_input_keyboard = Queue()
        # время существования клавиатуры
        self.timeout = timeout
        # время ожидания ответа от пользователя, None - ограничений нет, све время жизни клавиатуры
        self.user_timeout = user_timeout
        self.current_user: Optional["User"] = None
        # список пользователей
        self.users: Optional[list[int]] = []
        # объекты (другие клавиатуры) которые следят за нами
        self.tracked_objects: Optional[list[str]] = []
        self.data = {}
        # оставшееся время жизни клавиатуры
        self.expired: Optional[float] = 0
        self.is_running = False
        # Обновление клавиатуры отправлять всем или только новым
        self.is_dynamic = is_dynamic
        self.worker_task: Optional[Task] = None
        self.check_expired_task: Optional[Task] = None
        self.logger = logger or logging.getLogger(self.name)
        self.button_handler = {}
        self.event_handlers = {
            KeyboardEventEnum.update.value: self._event_update,
            KeyboardEventEnum.delete.value: self._event_delete,
            KeyboardEventEnum.new.value: self._event_new,
            KeyboardEventEnum.select.value: self._event_select,
        }
        self.text_handler = {None: self.text_all}
        self.is_redirect = []
        self.farewell_text = "Всем пока"
        # Событие произошло впервые (для того что бы можно было применить настройки, выбрать капитана)
        self.is_first = True
        self.timeout_keyboard = timeout_keyboard
        self.is_timeout = False

    async def poller_expired(self):
        """Закрывает workers по достижению timeout"""
        if not self.timeout:
            self.is_unlimited = True
        while self.is_running:
            try:
                if self.is_unlimited:
                    await sleep(self.timeout)
                else:
                    await sleep((self.expired + self.timeout) - monotonic())
                    # если есть клавиатура по таймауту
                    if self.timeout_keyboard:
                        self.is_running = False
                    elif (self.expired + self.timeout) < monotonic():
                        self.delete_inactive()
                        if len(self.users):
                            self.expired = monotonic()
                        else:
                            self.is_running = False
                self.expired = monotonic()
            except CancelledError:
                self.is_running = False
        if self.timeout_keyboard:
            ic(self.timeout_keyboard.keyboard.name, self.timeout_keyboard.user_ids)
            self.timeout_keyboard.user_ids = deepcopy(self.users)
            await self.redirect(**self.timeout_keyboard.as_dict())
            self.timeout_keyboard = None
        # Сообщаем клавиатура что мы все пошли спать так как в нас нет ни одного пользователя
        for keyboard_name in self.tracked_objects:
            await self.send_message_to_bot(
                MessageFromKeyboard(
                    keyboard_name=keyboard_name,
                    keyboard_event=KeyboardEventEnum.delete,
                    user_id=[0],
                    keyboards=[self.name],
                    body=self.farewell_text
                ))
        await self.bot.delete_keyboard(self.name)

    async def send_message_to_up(self, message: MessageToVK):
        if message.user_id not in self.is_redirect:
            if user := self.bot.get_user_by_id(message.user_id):
                await user.send_message_to_up(deepcopy(message))
                self.logger.warning(f"SEND_MESSAGE from: {self.name} to: {message.user_id}")
            else:
                self.logger.error(f"User not fount: {self.name} {message.user_id}")
        else:
            self.logger.debug(f"User is redirect: {message.user_id} {self.name}")

    async def send_message_to_up_for_all(self, message: MessageToVK):
        for user_id in self.users:
            message.user_id = user_id
            await self.send_message_to_up(message)

    def add_keyboard(self, keyboard_name: str) -> "Keyboard":
        """Добавляем Keyboard в список, кому приходят обновление по клавиатуре"""
        if keyboard_name not in self.tracked_objects:
            self.tracked_objects.append(keyboard_name)
        return self.get_keyboard(keyboard_name)

    def get_keyboard(self, keyboard_name: str) -> "Keyboard":
        """Получаем Клавиатуру, который находится в текущей клавиатуре"""
        if keyboard_name in self.tracked_objects:
            if keyboard := self.bot.get_keyboard_by_name(keyboard_name):
                return keyboard
            else:
                self.logger.error(f"Keyboard with id {keyboard_name} not found")

    def add_user(self, user_id: int) -> "User":
        """
        Добавляем User в список, кому приходят обновление по клавиатуре
        """
        if user_id not in self.users:
            self.users.append(user_id)
        return self.get_user(user_id)

    def get_user(self, user_id: int) -> "User":
        """
        Получаем пользователя, который находится в текущей клавиатуре
        """
        if user_id in self.users:
            if user := self.bot.get_user_by_id(user_id):
                return user
            else:
                self.logger.error(f"User with id {user_id} not found")

    async def delete_user(self, user_id: int):
        """Удаляем пользователя из списка users, в котором хранятся id пользователей слушающих клавиатуру,
        обычно это делается когда пользователь переходи в другую клавиатуру. Так же здесь происходит
        инициализация остановки работы клавиатуры если, в ней нет пользователей data пустой. Data -
        хранит данные о других клавиатурах которые влияют на текущею."""
        try:
            self.users.remove(user_id)
            self.logger.warning(f"{self.name} delete user id: {user_id} ")
        except ValueError:
            self.logger.error(f"User `{user_id}` not found in `{self.name}`")

    async def delete_keyboard(self, keyboard_name: str):
        try:
            self.tracked_objects.remove(keyboard_name)
        except ValueError:
            self.logger.warning(f"{self.name} keyboard {keyboard_name} not found")

    def create_message_to_vk(self, message: MessageFromVK) -> MessageToVK:
        """Генерация сообщения для VK"""
        message_to_vk = MessageToVK(
            user_id=message.user_id,
            body=message.body,
            keyboard=self.keyboard.as_str,
            type=message.type,
            event_id=message.event_id,
            peer_id=message.peer_id,
            event_data=message.event_data or message.payload.button_name,
        )
        return message_to_vk

    async def inbound_message_handler(self):
        while self.is_running:
            try:
                self.is_redirect = []
                message = await self.queue_input.get()
                # обновляем срок действия
                self.expired = monotonic()
                # сообщение касается VK
                if isinstance(message, (MessageFromVK,)):
                    event = await self.vk_message_handler(message)
                # сообщение касается текущей клавиатуры
                elif isinstance(message, (MessageFromKeyboard,)):
                    event = await self.keyboard_message_handler(message)
                else:
                    self.logger.warning(f"Skipping message: {message}")
                    continue
                # обновляем схему клавиатуры
                await self._update()
                # формируем сообщения для подписчиков Клавиатура, Пользователь
                if not event:
                    event = KeyboardEventEnum.select
                    self.logger.error(f"No value is set for `event`. {self.name} message type: {message}")
                message_to_keyboard, message_to_vk = await self.create_messages(event, message)
                # рассылка сообщений по подписчикам
                await self.send_message_to_all(message_to_vk, message_to_keyboard)
            except CancelledError:
                break

        await self.bot.delete_keyboard(self.name)

    async def create_messages(
            self,
            event: KeyboardEventEnum,
            message: Union[MessageFromVK, MessageFromKeyboard],
    ) -> ("MessageFromKeyboard", "MessageToVK"):
        user_id = (
            message.user_id
            if isinstance(message, MessageFromVK)
            else message.user_id[0]
        )
        event_id = message.event_id if isinstance(message, MessageFromVK) else None
        peer_id = message.peer_id if isinstance(message, MessageFromVK) else None
        event_data = (
            message.event_data if isinstance(message, MessageFromVK) else message.body
        )
        type_message = (
            message.type
            if isinstance(message, MessageFromVK)
            else TypeMessage.message_new
        )
        user_ids = (
            [message.user_id] if isinstance(message, MessageFromVK) else message.user_id
        )

        message_to_keyboard = MessageFromKeyboard(
            keyboard_name=self.name,
            keyboard_event=event,
            user_id=user_ids,
            body=message.body,
        )
        message_to_vk = self.create_message_to_vk(
            MessageFromVK(
                user_id=user_id,
                body=message.body,
                type=type_message,
                event_data=event_data or "Привет, ты был(а) долго не активен(а). Напиши чего ни будь",
                event_id=event_id,
                peer_id=peer_id,
            )
        )
        return message_to_keyboard, message_to_vk

    async def vk_message_handler(self, message: "MessageFromVK") -> KeyboardEventEnum:
        """Обработчик MessageFromVK"""
        # добавляем нового пользователя, которые находятся в меню
        user = self.add_user(message.user_id)
        # Задаем пользователю новое текущие место положения
        user.current_keyboard = self.name
        # выявляем нажатие на кнопку
        if message.payload.button_name:
            return await self.button_handlers(message)
        elif message.body:
            return await self.text_handlers(message)
        else:
            self.logger.error(f"Message error: {message}")
        return KeyboardEventEnum.select

    async def keyboard_message_handler(self, message: MessageFromKeyboard) -> KeyboardEventEnum:
        """Обрабатываем сообщений от клавиатур"""
        handler = self.event_handlers.get(message.keyboard_event.value)
        return await handler(message)

    async def text_handlers(self, message: MessageFromVK) -> "KeyboardEventEnum":
        # вызывает обработчик на входящею строку, или обработчик на все сообщения, если он описан
        handler = self.text_handler.get(message.body, None) or self.text_handler.get(
            None, None
        )
        return await handler(message)

    async def button_handlers(self, message: MessageFromVK) -> "KeyboardEventEnum":
        """Обработка нажатия кнопки"""
        if handler := self.button_handler.get(message.payload.button_name):
            return await handler(message)
        # тогда проверяем не нажали event кнопку, и запускаем шаблон
        elif message.type.value == TypeMessage.message_event.value:
            return await self.button_template_title(message)
        self.bot.logger.warning(
            f"Button not found keyboard={message.payload.keyboard_name}, button_name={message.payload.button_name}"
        )
        return KeyboardEventEnum.select

    async def send_message_to_keyboards(self, message: MessageFromKeyboard):

        """Отправка сообщения всем подписанным клавиатурам"""
        for keyboard_name in self.tracked_objects.copy():
            if keyboard := self.bot.get_keyboard_by_name(keyboard_name):
                await keyboard.send_message_to_down(message)
            else:
                # если клавиатура перестала жить удаляем ее из своих подписчиков
                self.bot.logger.warning(keyboard_name)
                self.tracked_objects.remove(keyboard_name)

    async def send_message_to_users(self, message: MessageToVK):
        """Отправка сообщений пользователям, в соответствии с настройками клавиатуры"""
        # Если клавиатура обновляется для всех пользователей и является динамичной
        if self.is_dynamic:
            await self.send_message_to_up_for_all(message)
        else:
            await self.send_message_to_up(message)

    async def send_message_to_all(self, message_to_vk: MessageToVK, message_to_keyboard: MessageFromKeyboard):
        """Отправка сообщений всем подписчикам"""
        # рассылаем сообщения по клавиатурам только если событие не SELECT
        if message_to_keyboard.keyboard_event.value != KeyboardEventEnum.select.value:
            await self.send_message_to_keyboards(message_to_keyboard)
        else:
            self.logger.warning(f"SELECT {self.name} message not send")
        # рассылка users
        await self.send_message_to_users(message_to_vk)

    async def _update(self):
        self.bot.logger.warning(f"UPDATE START {self.name} users={self.users} keyboards {self.tracked_objects}")
        await self.update()
        self.bot.logger.warning(f"UPDATE END {self.name} users={self.users} keyboards {self.tracked_objects}")

    async def update(self):
        self.bot.logger.warning(f"UPDATE {self.name} users={self.users} keyboards {self.tracked_objects}")

    async def _event_update(self, message: MessageFromKeyboard):
        self.bot.logger.warning(f"UPDATE_EVENT {self.name} {message}")
        event = await self.event_update(message)
        self.bot.logger.debug(f"UPDATE_EVENT {self.name} Complete, message: {message}")
        return event

    async def event_update(self, message: MessageFromKeyboard):
        """В клавиатуре за которой мы наблюдаем произошли изменения, кто-то вышел, вошел"""
        return KeyboardEventEnum.select

    async def _event_delete(self, message: MessageFromKeyboard):
        self.bot.logger.warning(f"DELETE_EVENT {self.name} {message}")
        event = await self.event_delete(message)
        self.bot.logger.debug(f"DELETE_EVENT {self.name} Complete, message: {message}")
        return event

    async def event_delete(self, message: MessageFromKeyboard):
        return KeyboardEventEnum.select

    async def _event_new(self, message: MessageFromKeyboard) -> KeyboardEventEnum:
        self.bot.logger.debug(f"EVENT NEW {self.name} start...")
        # обходим всех пользователей, и добавляем их в клавиатуру
        if message.user_id:
            for user_id in message.user_id:
                user = self.add_user(user_id)
                user.current_keyboard = self.name
                # Назначаем настройки по умолчанию, если их нет у пользователя
                if not user.get_setting_keyboard(self.__class__.name):
                    user.set_setting_keyboard(self.__class__.name, self.get_keyboard_default_setting())
        # обходим все клавиатуры, и добавляем их в клавиатуру
        if message.keyboards:
            for keyboard_name in message.keyboards:
                self.add_keyboard(keyboard_name)

        # вызываем пользовательский обработчик на событие
        event = await self.event_new(message)
        self.bot.logger.debug(f"EVENT NEW {self.name} Complete, message: {message}")
        # Означает что в нашей клавиатуре есть обновления, для тех кто подписан на нас
        return event

    async def event_new(self, message: MessageFromKeyboard) -> KeyboardEventEnum:
        return KeyboardEventEnum.update

    async def _event_select(self, message: MessageFromKeyboard) -> KeyboardEventEnum:
        self.bot.logger.warning(f"SELECT_EVENT {self.name} {message}")
        event = await self.event_select(message)
        self.bot.logger.debug(f"SELECT_EVENT {self.name} Complete, message: {message}")
        return event

    async def event_select(self, message: MessageFromKeyboard) -> KeyboardEventEnum:  # noqa
        """Обработка (реакция) события SELECT"""
        return KeyboardEventEnum.select

    async def text_all(self, message: MessageFromVK) -> KeyboardEventEnum:
        self.bot.logger.warning(f"TEXT_ALL {self.name} {message}")
        return KeyboardEventEnum.select

    async def button_template_title(self, message: MessageFromVK) -> KeyboardEventEnum:
        """Шаблон для отправки ответа на нажатие кнопки Title, загоняем в event_data - help_string из base_structure"""
        self.logger.debug(f"{self.name} TITLE")
        message.event_data = self.keyboard.get_help_string_from_title(
            message.payload.button_name
        )
        return KeyboardEventEnum.select

    async def send_message_to_bot(self, message: Union[MessageFromVK, MessageFromKeyboard]):
        """Сообщение для бота, данное сообщение будет обработано в inbound_message_handler"""
        await self.bot.queue_input.put(message)

    async def redirect(
            self,
            keyboard: Union[Type["Keyboard"], "Keyboard"],
            user_ids: list[int],
            keyboards: list[int] = None,
            is_dynamic: bool = False,
            is_private: bool = False,
            body: str = None,
            settings: "GameSessionSettings" = None,
            kill_parent: str = None,
    ) -> KeyboardEventEnum.new:
        """
        Переводит игрока или группу игроков в другую клавиатуру.
        :param keyboard: Клавиатура назначения.
        :param user_ids: Список id User, которые переходят в новую клавиатуру.
        :param keyboards: Список name Keyboard, которые просят данные при появлениях в новой клавиатуре изменениях.
        :param is_dynamic: True - изменения транслируются всем слушателям
        :param is_private: True - клавиатура персональная.
        :param body: Текст, который будет отображаться при переходе в новой клавиатуре
        :param settings: Настройки, которые нужно передать в новую клавиатуру
        :return:
        """
        # создаем или вытаскиваем из бота клавиатуру в которую направляем пользователей
        if user_ids:
            keyboard_name = (keyboard.name + str(user_ids[0]) if is_private else keyboard.name)
            keyboard = self.bot.get_keyboard_by_name(
                keyboard_name
            ) or await self.bot.create_keyboard(
                keyboard_name=keyboard_name,
                keyboard=keyboard,
                keyboard_timeout=self.bot.keyboard_expired,
                user_timeout=self.bot.user_expired,
                is_dynamic=is_dynamic,
            )
            # если есть настройки
            if settings:
                keyboard.data["settings"] = settings
            # Удаляем пользователей из текущей клавиатуры
            for user_id in user_ids:
                await self.delete_user(user_id)

            # отправляем через бот сообщение о том что добавили пользователей в новую клавиатуру, и клавиатуры
            if is_dynamic:
                await self.send_message_to_bot(
                    MessageFromKeyboard(
                        keyboard_name=keyboard.name,
                        keyboard_event=KeyboardEventEnum.new,
                        user_id=user_ids,
                        keyboards=keyboards,
                        body=body or f"You are in the menu {keyboard.name}"
                    )
                )
            else:
                for user_id in user_ids:
                    await self.send_message_to_bot(
                        MessageFromKeyboard(
                            keyboard_name=keyboard.name,
                            keyboard_event=KeyboardEventEnum.new,
                            user_id=[user_id],
                            keyboards=keyboards,
                            body=body or f"You are in the menu {keyboard.name}"
                        )
                    )
            # Событие, которое будет обрабатывать навоя клавиатура куда прилит сообщение
            self.logger.error(f"Redirect FROM {self.name} TO {keyboard.name}")
            # сигнал о том что пользователю сообщение не отправлять, нужно для того
            # что бы он не вернулся после редиректа
            self.is_redirect = user_ids
            if kill_parent:
                await self.bot.delete_keyboard(kill_parent)
            return KeyboardEventEnum.new
        else:
            # keyboard_name = (keyboard.name + str(randint(1000, 100000)) if is_private else keyboard.name)
            self.logger.critical(f"{self.name}: Error namespace : {user_ids}, {keyboard.name}")
            return KeyboardEventEnum.select

    def get_setting_keyboard(self) -> Union["GameSessionSettings", "TeamIsReady", "Round"]:
        """Вытаскиваем из User настройки Keyboard, они так же актуальны для игры, если они есть мы их возвращаем,
        иначе применяем настройки по умолчанию"""
        if self.users:
            if user := self.get_user(self.users[0]):
                if settings := user.get_setting_keyboard(self.__class__.name):
                    return settings
                else:
                    return self.get_keyboard_default_setting()
            self.logger.error(f"User not found: {self.users[0]}")

    def get_keyboard_default_setting(self) -> Union["GameSessionSettings", "Round"]:
        """Настройки клавиатуры по умолчанию, место куда скидывают настройки по умолчанию для клавиатур"""
