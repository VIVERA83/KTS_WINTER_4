from copy import deepcopy
from typing import Union

from bot.data_classes import KeyboardEventEnum, MessageFromVK
from bot.vk.keyboards.data_classes import TeamIsReady, TimeoutKeyboard
from bot.vk.keyboards.round_game import RoundGameKeyboard
from bot.vk.vk_keyboard.buttons import Button, Title
from bot.vk.vk_keyboard.data_classes import TypeColor
from bot.vk.vk_keyboard.keyboard import Keyboard as KeyboardSchema
from bot.workers.keyboard import Keyboard
from icecream import ic

ic.includeContext = True
base_structure = {
    0: [
        Title(
            name="Проверка готовности",
            label="Проверка готовности",
            color=TypeColor.white,
            help_string="Игра начнется по готовности, либо в течении 1 минуты",
        )
    ],
}


class TeamIsReadyKeyboard(Keyboard):
    name = "TeamIsReadyKeyboard"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.keyboard = KeyboardSchema(name="TeamIsReadyKeyboard", buttons=base_structure, one_time=False)
        self.timeout_keyboard = TimeoutKeyboard(keyboard=RoundGameKeyboard,
                                                user_ids=self.users,
                                                is_dynamic=True,
                                                is_private=True,
                                                )

    async def button_ready(self, message: "MessageFromVK") -> "KeyboardEventEnum":
        """Кнопка назначенная на Готов"""
        if message.payload.button_name == str(message.user_id) + "_":
            message.body = f"{self.get_user(message.user_id).name} ГОТОВ"
            settings = self.get_keyboard_default_setting()
            settings.buttons[message.payload.button_name] = not settings.buttons[message.payload.button_name]
        else:
            message.body = f"{self.get_user(message.user_id).name} не хорошо чужую кнопочку жать"
        return KeyboardEventEnum.select

    def get_keyboard_default_setting(self) -> Union["TeamIsReady"]:
        """Настройки клавиатуры по умолчанию, место куда скидывают настройки по умолчанию для клавиатур"""
        settings = self.data.get("settings", TeamIsReady())
        for button_name in self.button_handler.keys():
            if not settings.buttons.get(button_name):
                settings.buttons[button_name] = False
        self.data["settings"] = settings
        return self.data["settings"]

    async def update(self):
        """Глобальное обновление клавиатуры"""
        await self.update_buttons()
        # если команда готова, переводи ее в игру
        if all(self.get_keyboard_default_setting().buttons.values()):
            await self.redirect(RoundGameKeyboard, deepcopy(self.users), is_dynamic=True, is_private=True, )



    async def update_buttons(self):
        """Обновляем состояние кнопок, 1 кнопка 1 пользователь"""
        buttons = deepcopy(base_structure)
        self.button_handler = dict()
        for key, user_id in enumerate(self.users, 1):
            user = self.get_user(user_id)
            title = Title(
                name=str(user_id),
                label=user.name,
                color=TypeColor.white,
                help_string="Жми скорей Готов....",
            )
            button = Button(
                name=str(user_id) + "_",
                label="Готов",
                color=TypeColor.blue,
            )
            buttons[key] = [title, button]
            self.button_handler[str(user_id) + "_"] = self.button_ready
        self.keyboard.buttons = buttons
        self.change_color()

    def change_color(self):
        """Меняет цвет кнопки, если кнопка есть в настройках мы ей задаем цвет"""
        settings = self.get_keyboard_default_setting()
        for buttons in self.keyboard.buttons.values():
            for button in buttons:
                change = settings.buttons.get(button.name, None)
                if change is not None:
                    button.color = TypeColor.green if change else TypeColor.red
