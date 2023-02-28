from typing import TYPE_CHECKING

from bot.data_classes import MessageFromVK
from bot.utils import redirect
from bot.vk.vk_keyboard.buttons import Button, Title
from bot.vk.vk_keyboard.data_classes import TypeColor
from bot.vk.vk_keyboard.keyboard import Keyboard as KeyboardSchema
from bot.workers.keyboard import Keyboard

from .join_game import JoinGameKeyboard

if TYPE_CHECKING:
    from bot.workers.dispatcher import Bot


class RootKeyboard(Keyboard):
    name = "RootKeyboard"
    base_structure = {
        0: [
            Title(
                name="Заголовок",
                label="Основное меню",
                color=TypeColor.white,
                help_string="Привет, отсюда начинается работа с ботом",
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
    keyboard = KeyboardSchema(
        name="RootKeyboard", buttons=base_structure, one_time=False
    )

    button_handler = {
        "Создать игру": lambda bot, message: button_create_game(bot, message),
        "Присоединится": lambda bot, message: redirect(
            bot=bot,
            message=message,
            current_keyboard=bot.root_keyboard.name,
            next_keyboard=JoinGameKeyboard,
        ),
    }
    text_handler = {
        "Hello World": lambda bot, message: button_create_game(bot, message),
        None: lambda *args, **kwargs: all_text(*args, **kwargs),
    }


async def button_create_game(bot: "Bot", message: MessageFromVK):
    bot.logger.warning("Start")


async def all_text(bot: "Bot", message: MessageFromVK):
    bot.logger.warning(message.body)
