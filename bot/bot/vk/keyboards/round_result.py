from copy import deepcopy

from icecream import ic

from bot.data_classes import KeyboardEventEnum, MessageFromVK, MessageFromKeyboard
from bot.vk.keyboards.data_classes import TimeoutKeyboard, Round
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
            help_string="количество очков, заработанные командами зрителей и знатоков"
        ),
    ],
    2: [
        Title(
            name="Знатоки",
            label="Знатоки",
            color=TypeColor.green,
            help_string="Общее количество очков кашей команды"
        ),
        Title(
            name="Зрители",
            label="Зрители",
            color=TypeColor.white,
            help_string="Ошибки Вашей команды"
        ),
    ],
    3: [
        Title(
            name="Очки знатоков",
            label="0",
            color=TypeColor.green,
            help_string="И как вас результат"
        ),
        Title(
            name="Очки зрителей",
            label="0",
            color=TypeColor.red,
            help_string="И как вас результат"
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
    settings: "Round"

    def __init__(self, *args, **kwargs):
        from bot.vk.keyboards.round_game import RoundGameKeyboard
        super().__init__(*args, **kwargs)
        self.keyboard = KeyboardSchema(name="RoundResultKeyboard", buttons=base_structure, one_time=False)
        self.button_handler = {"Ok": self.button_ok}
        self.timeout_keyboard = TimeoutKeyboard(keyboard=RoundGameKeyboard,
                                                user_ids=self.users,
                                                is_private=True,
                                                is_dynamic=True,
                                                )

    async def button_ok(self, message: "MessageFromVK") -> "KeyboardEventEnum":
        from bot.vk.keyboards.root import RootKeyboard
        if self.settings.session_setting.rounds.value <= self.settings.number:
            await self.redirect(keyboard=RootKeyboard, user_ids=deepcopy(self.users), kill_parent=self.name)
        else:
            return await self.redirect(keyboard=self.timeout_keyboard.keyboard, user_ids=deepcopy(self.users),
                                       is_private=True,
                                       is_dynamic=True,
                                       kill_parent=self.name)

    async def event_new(self, message: MessageFromKeyboard) -> KeyboardEventEnum:
        await self.first_run_keyboard(message)
        return KeyboardEventEnum.update

    async def first_run_keyboard(self, message: MessageFromKeyboard):
        if self.is_first:
            if self.users:
                self.is_first = False
                self.settings = self.get_setting_keyboard()
                self.is_end_game()
                self.create_buttons()
            else:
                self.logger.error(f"The list of users is empty: {self.users}")

    def get_keyboard_default_setting(self) -> "Round":
        """Достать настройки игры из пользователя из первого"""
        from bot.vk.keyboards.round_game import RoundGameKeyboard
        self.settings = self.get_user(self.users[0]).get_setting_keyboard(RoundGameKeyboard.name)
        return self.settings

    def create_buttons(self):
        """Создаем кнопки"""
        buttons = deepcopy(base_structure)
        buttons[3][0].label = f"{self.settings.experts}"
        buttons[3][1].label = f"{self.settings.watcher}"

        if self.settings.session_setting.rounds.value <= self.settings.number:
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
        if self.settings.session_setting.rounds.value <= self.settings.number:
            self.timeout_keyboard = TimeoutKeyboard(keyboard=RootKeyboard, user_ids=self.users)
