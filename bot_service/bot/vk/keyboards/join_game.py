from typing import TYPE_CHECKING

from bot.data_classes import MessageFromVK
from bot.utils import redirect
from bot.vk.vk_keyboard.buttons import Button, Title
from bot.vk.vk_keyboard.data_classes import TypeColor
from bot.vk.vk_keyboard.keyboard import Keyboard as KeyboardSchema
from bot.workers.keyboard import Keyboard

if TYPE_CHECKING:
    from bot.workers.dispatcher import Bot
base_structure = {
    0: [
        Title(
            name="Заголовок",
            label="Присоединится к игре",
            color=TypeColor.white,
            help_string="Список игровых сессий ожидающих тебя, для выбора кликни по кнопке",
        )
    ],
    1: [
        Button(
            name="Назад",
            label="Назад",
            color=TypeColor.red,
        )
    ],
}


class JoinGameKeyboard(Keyboard):
    name = "JoinGameKeyboard"
    keyboard = KeyboardSchema("JoinGameKeyboard", base_structure, False)

    button_handler = {"Назад": lambda *args, **kwargs: button_back(*args, **kwargs)}


async def button_back(bot: "Bot", message: MessageFromVK, *_: list, **__: dict):
    from bot.vk.keyboards.root import RootKeyboard

    await redirect(
        bot=bot,
        message=message,
        current_keyboard="JoinGameKeyboard",
        next_keyboard=RootKeyboard,
    )

    #
    # if old_keyboard := bot.get_keyboard_by_name("JoinGameKeyboard"):
    #     old_keyboard.delete_user(message.user_id)
    #
    # keyboard = bot.get_keyboard_by_name("RootKeyboard")
    # if not keyboard:
    #     keyboard = RootKeyboard(bot=bot,
    #                             name="RootKeyboard",
    #                             timeout=bot.keyboard_expired,
    #                             user_timeout=bot.user_expired,
    #                             is_dynamic=False)
    #     await keyboard.start()
    #     bot.add_keyboard(keyboard)
    #
    # message.payload.keyboard_name = keyboard.name
    # message.payload.button_name = None
    # await keyboard.send_message_to_down(message)
