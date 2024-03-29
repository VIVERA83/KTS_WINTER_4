import logging
from copy import deepcopy
from typing import Union, Optional

from bot.data_classes import MessageFromVK, KeyboardEventEnum, MessageFromKeyboard
from bot.vk.keyboards.data_classes import GameSessionSettings, Data, TimeoutKeyboard
from bot.vk.keyboards.utils import change_color
from bot.vk.vk_keyboard.buttons import Button, Title
from bot.vk.vk_keyboard.data_classes import TypeColor
from bot.vk.vk_keyboard.keyboard import Keyboard as KeyboardSchema
from bot.workers.dispatcher import Bot
from bot.workers.keyboard import Keyboard

base_structure = {
    0: [
        Title(
            name="Настройка",
            label="Настройка",
            color=TypeColor.white,
            help_string="Здесь вы можете настроить игру, выбрать размер команды и количества раундов",
        )
    ],
    1: [
        Title(
            name="Размер команды",
            label="Размер команды",
            color=TypeColor.white,
            help_string="Чем больше команда тем веселей играть ",
        )
    ],
    2: [
        Button(
            name="1 players",
            label="1",
            color=TypeColor.blue,
        ),
        Button(
            name="2 players",
            label="2",
            color=TypeColor.blue,
        ),
        Button(
            name="5 players",
            label="5",
            color=TypeColor.blue,
        ),
    ],
    3: [
        Title(
            name="Количество раундов",
            label="Количество раундов",
            color=TypeColor.white,
            help_string="Выберите продолжительность игры",
        )
    ],
    4: [
        Button(
            name="3 rounds",
            label="3",
            color=TypeColor.blue,
        ),
        Button(
            name="5 rounds",
            label="5",
            color=TypeColor.blue,
        ),
        Button(
            name="7 rounds",
            label="7",
            color=TypeColor.blue,
        ),
    ],
    5: [
        Button(
            name="Создать",
            label="Создать",
            color=TypeColor.green,
        ),
        Button(
            name="Назад",
            label="Назад",
            color=TypeColor.red,
        ),
    ],
}


class GameSessionSettingKeyboard(Keyboard):
    name = "GameSessionSettingKeyboard"

    def __init__(
            self,
            bot: "Bot",
            name: str,
            timeout: int,
            user_timeout: int = None,
            is_dynamic: bool = False,
            logger: Optional[logging.Logger] = None,
            timeout_keyboard: Optional["TimeoutKeyboard"] = None,
    ):
        super().__init__(
            bot, name, timeout, user_timeout, is_dynamic, logger, timeout_keyboard
        )
        self.keyboard = KeyboardSchema(
            name=self.name, buttons=deepcopy(base_structure), one_time=False
        )
        self.button_handler = {
            "1 players": lambda message: self.button_update_players(message, 1),
            "2 players": lambda message: self.button_update_players(message, 2),
            "5 players": lambda message: self.button_update_players(message, 5),
            "3 rounds": lambda message: self.button_update_rounds(message, 3),
            "5 rounds": lambda message: self.button_update_rounds(message, 5),
            "7 rounds": lambda message: self.button_update_rounds(message, 7),
            "Создать": self.button_create_game,
            "Назад": self.button_back,
        }
        self.settings: Optional[GameSessionSettings] = None

    async def event_new(self, message: MessageFromKeyboard) -> KeyboardEventEnum:
        await self.first_run_keyboard(message)
        return KeyboardEventEnum.update

    async def first_run_keyboard(self, message: MessageFromKeyboard):
        if self.is_first:
            if self.users:
                self.is_first = False
                self.settings = await self.get_keyboard_default_setting()
            else:
                self.logger.error(f"The list of users is empty: {self.users}")

    async def button_back(self, message: MessageFromVK):
        """Вернуться в RootKeyboard"""
        from bot.vk.keyboards.root import RootKeyboard

        self.get_user(message.user_id).set_setting_keyboard(
            self.__class__.name, self.settings
        )
        return await self.redirect(RootKeyboard, [message.user_id])

    async def button_update_players(
            self, message: MessageFromVK, value: int
    ) -> "KeyboardEventEnum":
        """Изменение количества игроков в игре и клавиатуры"""
        # Назначаем новое значение в настройках и в клавиатуре
        self.settings.players.value = value
        self.settings.players.button_name = message.payload.button_name
        message.body = f"Изменен размер команды, теперь {value}"
        return KeyboardEventEnum.select

    async def button_update_rounds(
            self, message: MessageFromVK, value: int
    ) -> "KeyboardEventEnum":
        """Изменение количества раундов в игре и клавиатуры"""
        # Назначаем новое значение в настройках и в клавиатуре
        self.settings.rounds.value = value
        self.settings.rounds.button_name = message.payload.button_name
        message.body = f"Изменено количество раундов в игре на {value}"
        return KeyboardEventEnum.select

    async def button_create_game(self, message: MessageFromVK) -> "KeyboardEventEnum":
        """Создаем игровую комнату в которой набирается команда"""
        from bot.vk.keyboards.team_server import TeamServerKeyboard
        from bot.vk.keyboards.join_game import JoinGameKeyboard

        # проверим если такая активная клавиатура, если нет создаем, она будет слушать TeamCompositionServerKeyboard
        self.bot.get_keyboard_by_name(
            JoinGameKeyboard.name
        ) or await self.bot.create_keyboard(
            keyboard_name=JoinGameKeyboard.name,
            keyboard=JoinGameKeyboard,
            keyboard_timeout=self.bot.keyboard_expired,
            user_timeout=self.bot.user_expired,
            is_dynamic=True,
        )
        self.get_user(message.user_id).set_setting_keyboard(
            self.__class__.name, self.settings
        )
        # Переводим игрока в TeamCompositionServerKeyboard,
        return await self.redirect(
            TeamServerKeyboard,
            [message.user_id],
            [JoinGameKeyboard.name],
            True,
            True,
        )

    async def update(self):
        change_color(self, TypeColor.green, TypeColor.blue, self.settings)

    async def get_keyboard_default_setting(self) -> Union["GameSessionSettings"]:
        """Настройки клавиатуры по умолчанию, место куда скидывают настройки по умолчанию для клавиатур"""
        return GameSessionSettings(
            players=Data(value=1, row=2, button_name="1 players"),
            rounds=Data(value=5, row=4, button_name="5 rounds"),
        )
