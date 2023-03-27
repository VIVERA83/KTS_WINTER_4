from copy import deepcopy
from typing import Optional

from api_game_www.data_classes import RoundRequest
from bot.data_classes import KeyboardEventEnum, MessageFromVK, MessageFromKeyboard
from bot.vk.keyboards.data_classes import TimeoutKeyboard, GameData
from bot.vk.vk_keyboard.buttons import Button, Title
from bot.vk.vk_keyboard.data_classes import TypeColor
from bot.vk.vk_keyboard.keyboard import Keyboard as KeyboardSchema
from bot.workers.keyboard import Keyboard

base_structure = {
    0: [
        Title(
            # Победа или поражение в раунде
            name="Результат",
            label="Результат ",
            color=TypeColor.white,
            help_string="Итоги раунда",
        )
    ],
    1: [
        Title(
            name="Предварительный счет",
            label="Предварительный счет",
            color=TypeColor.white,
            help_string="количество очков, заработанные командами зрителей и знатоков",
        ),
    ],
    2: [
        Title(
            name="Знатоки",
            label="Знатоки",
            color=TypeColor.green,
            help_string="Общее количество очков кашей команды",
        ),
        Title(
            name="Зрители",
            label="Зрители",
            color=TypeColor.white,
            help_string="Ошибки Вашей команды",
        ),
    ],
    3: [
        Title(
            name="Очки знатоков",
            label="0",
            color=TypeColor.green,
            help_string="И как вас результат",
        ),
        Title(
            name="Очки зрителей",
            label="0",
            color=TypeColor.red,
            help_string="И как вас результат",
        ),
    ],
    4: [
        Button(
            name="Ok",
            label="Ok",
            color=TypeColor.white,
        )
    ],
}


class RoundResultKeyboard(Keyboard):
    name = "RoundResultKeyboard"

    def __init__(self, *args, **kwargs):
        from bot.vk.keyboards.round_game import RoundGameKeyboard

        super().__init__(*args, **kwargs)
        self.keyboard = KeyboardSchema(
            name=self.name, buttons=base_structure, one_time=False
        )
        self.button_handler = {"Ok": self.button_ok}
        self.timeout_keyboard = TimeoutKeyboard(
            keyboard=RoundGameKeyboard,
            user_ids=self.users,
            is_private=True,
            is_dynamic=True,
        )
        self.settings: Optional["GameData"] = None

    async def button_ok(self, message: "MessageFromVK") -> "KeyboardEventEnum":
        from bot.vk.keyboards.root import RootKeyboard

        if self.settings.game_session.rounds.value <= self.settings.round.number:
            await self.redirect(
                keyboard=RootKeyboard, user_ids=deepcopy(self.users), kill_parent=True
            )
        else:
            return await self.redirect(
                keyboard=self.timeout_keyboard.keyboard,
                user_ids=deepcopy(self.users),
                is_private=True,
                is_dynamic=True,
                kill_parent=True,
            )

    async def event_new(self, message: MessageFromKeyboard) -> KeyboardEventEnum:
        await self.first_run_keyboard(message)
        return KeyboardEventEnum.update

    async def first_run_keyboard(self, message: MessageFromKeyboard):
        if self.is_first:
            if self.users:
                self.is_first = False
                self.settings = await self.get_keyboard_default_setting()
                self.create_buttons()
                self.is_end_game()
                await self.bot.app.store.api_game_www.save_round_result(RoundRequest(
                    respondent_id=self.settings.capitan,
                    answer=self.settings.round.answer,
                    question_id=self.settings.question.id,
                    game_session_id=self.settings.game_session.id
                ))
            else:
                self.logger.error(f"The list of users is empty: {self.users}")

    async def get_keyboard_default_setting(self) -> "GameData":
        """Достать настройки игры из пользователя из первого"""
        from bot.vk.keyboards.round_game import RoundGameKeyboard

        return self.get_user(self.users[0]).get_setting_keyboard(RoundGameKeyboard.name)

    def create_buttons(self):
        """Создаем кнопки"""
        buttons = deepcopy(base_structure)
        buttons[3][0].label = f"{self.settings.experts}"
        buttons[3][1].label = f"{self.settings.watcher}"

        if self.settings.game_session.rounds.value <= self.settings.round.number:
            buttons[0][0].label = "Итоговый результат игры"
            if self.settings.watcher < self.settings.experts:
                buttons[1][0].label = "ПОБЕДА"
                buttons[1][0].color = TypeColor.green
            elif self.settings.watcher > self.settings.experts:
                buttons[1][0].label = "ПОРАЖЕНИЕ"
                buttons[1][0].color = TypeColor.red
            else:
                buttons[1][0].label = "НИЧЬЯ"
                buttons[1][0].color = TypeColor.blue
        self.keyboard.buttons = buttons

    def is_end_game(self):
        from bot.vk.keyboards.root import RootKeyboard
        if self.settings.game_session.rounds.value <= self.settings.round.number:
            self.timeout_keyboard = TimeoutKeyboard(
                keyboard=RootKeyboard, user_ids=self.users
            )
            for user_id in self.users:
                settings = self.get_user(user_id).get_setting_keyboard(self.__class__.__name__)
                settings.round.number = 0
                settings.watcher = 0
                settings.experts = 0
                settings.question = None
                settings.round.answer = None
