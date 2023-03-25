from bot.data_classes import KeyboardEventEnum, MessageFromVK
from bot.vk.vk_keyboard.buttons import Button, Title
from bot.vk.vk_keyboard.data_classes import TypeColor
from bot.vk.vk_keyboard.keyboard import Keyboard as KeyboardSchema
from bot.workers.keyboard import Keyboard

base_structure = {
    0: [
        Title(
            name="Что? Где? Когда?",
            label="Что? Где? Когда?",
            color=TypeColor.white,
            help_string="Вы здесь, потому что Вы долго не проявляли активность. Добро пожаловать",
        )
    ],
    1: [
        Button(
            name="Ok",
            label="OK",
            color=TypeColor.green,
        ),
    ],
}


class LogOutKeyboard(Keyboard):
    name = "LogOutKeyboard"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.keyboard = KeyboardSchema(
            name="LogOutKeyboard", buttons=base_structure, one_time=False
        )
        self.button_handler = {
            "Ok": self.button_ok,
        }

    async def button_ok(self, message: "MessageFromVK") -> "KeyboardEventEnum":
        from bot.vk.keyboards.root import RootKeyboard

        return await self.redirect(keyboard=RootKeyboard, user_ids=[message.user_id])
