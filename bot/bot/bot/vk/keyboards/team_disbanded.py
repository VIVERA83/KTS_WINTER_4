from bot.data_classes import MessageFromVK, KeyboardEventEnum
from bot.vk.keyboards.data_classes import TimeoutKeyboard
from bot.vk.vk_keyboard.buttons import Button, Title
from bot.vk.vk_keyboard.data_classes import TypeColor
from bot.vk.vk_keyboard.keyboard import Keyboard as KeyboardSchema
from bot.workers.keyboard import Keyboard

base_structure = {
    0: [
        Title(
            name="Команда распущена",
            label="Команда распущена",
            color=TypeColor.white,
            help_string="Команда бы распущена по инициативе основателя",
        )
    ],
    1: [
        Button(
            name="Ок",
            label="Ок",
            color=TypeColor.green,
        ),
    ],
}


class TeamDisbandedKeyboard(Keyboard):
    name = "TeamDisbandedKeyboard"

    def __init__(self, *args, **kwargs):
        from bot.vk.keyboards.logout import LogOutKeyboard

        super().__init__(*args, **kwargs)
        self.keyboard = KeyboardSchema(
            name=self.name, buttons=base_structure, one_time=False
        )
        self.button_handler = {
            "Ок": self.button_ok,
        }
        self.timeout_keyboard = TimeoutKeyboard(
            keyboard=LogOutKeyboard,
            user_ids=self.users,
        )

    async def button_ok(self, message: MessageFromVK) -> "KeyboardEventEnum":
        from bot.vk.keyboards.root import RootKeyboard

        return await self.redirect(RootKeyboard, [message.user_id])
