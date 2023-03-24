from bot.data_classes import KeyboardEventEnum, MessageFromVK
from bot.vk.vk_keyboard.buttons import Button, Title
from bot.vk.vk_keyboard.data_classes import TypeColor
from bot.vk.vk_keyboard.keyboard import Keyboard as KeyboardSchema
from bot.workers.keyboard import Keyboard

base_structure = {
    0: [
        Title(
            name="Основное меню",
            label="Основное меню",
            color=TypeColor.white,
            help_string="Вы здесь, потому что Вас долго не было либо только пришли. Добро пожаловать",
        )
    ],
    1: [
        Button(
            name="Создать игру",
            label="Создать игру",
            color=TypeColor.green,
        ),
        Button(
            name="Присоединится",
            label="Присоединится",
            color=TypeColor.green,
        ),
    ],
}


class RootKeyboard(Keyboard):
    name = "RootKeyboard"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.keyboard = KeyboardSchema(name="RootKeyboard", buttons=base_structure, one_time=False)
        self.button_handler = {
            "Создать игру": self.button_greate_game,
            "Присоединится": self.button_join_game,
        }

    async def button_greate_game(self, message: "MessageFromVK") -> "KeyboardEventEnum":
        from bot.vk.keyboards.game_session_settings import GameSessionSettingKeyboard
        return await self.redirect(keyboard=GameSessionSettingKeyboard, user_ids=[message.user_id], is_private=True)

    async def button_join_game(self, message: "MessageFromVK") -> "KeyboardEventEnum":
        from bot.vk.keyboards.join_game import JoinGameKeyboard
        return await self.redirect(keyboard=JoinGameKeyboard, user_ids=[message.user_id], is_dynamic=True)
