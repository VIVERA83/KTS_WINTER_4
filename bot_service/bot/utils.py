from typing import Type

from bot.data_classes import MessageFromVK
from bot.workers.dispatcher import Bot
from bot.workers.keyboard import Keyboard


async def redirect(
    bot: "Bot",
    message: MessageFromVK,
    current_keyboard: str,
    next_keyboard: Type[Keyboard],
):
    """
    Перенаправление, на другую клавиатуру.
    :param bot:
    :param message:
    :param current_keyboard: Имя текущей клавиатуры в которой вызывается данное действие.
    :param next_keyboard: Клавиатура в которую перенаправляем.
    :return:
    """
    # текущая клавиатура, из которой происходит переход
    if old_keyboard := bot.get_keyboard_by_name(current_keyboard):
        # удаляем пользователя из участников, которым прилетают обновление по данной клавиатуре
        old_keyboard.delete_user(message.user_id)
    # вызываем клавиатуру в которую намерены перейти, если ее нет, создаем
    keyboard = bot.get_keyboard_by_name(
        next_keyboard.keyboard.name
    ) or await bot.create_keyboard(
        keyboard_name=next_keyboard.keyboard.name,
        keyboard=next_keyboard,
        keyboard_timeout=bot.keyboard_expired,
        user_timeout=bot.user_expired,
        is_dynamic=False,
    )
    # заменяем данные в сообщение на те в которую переназначен
    message.payload.keyboard_name = keyboard.name
    #  сообщает нам что user не производил нажатие на кнопки
    message.payload.button_name = None
    # перенаправляем сообщение в клавиатуру в которую происходит перенаправление
    await keyboard.send_message_to_down(message)
