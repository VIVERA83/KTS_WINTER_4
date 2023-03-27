from typing import TYPE_CHECKING, Union

from bot.vk.keyboards.data_classes import GameSessionSettings
from bot.vk.vk_keyboard.data_classes import TypeColor

from bot.workers.keyboard import Keyboard

if TYPE_CHECKING:
    from bot.vk.vk_keyboard.keyboard import Keyboard


def change_color(
    keyboard: Keyboard,
    color_active: TypeColor,
    color_disabled: TypeColor,
    settings: Union["GameSessionSettings"],
):
    """
    Меняем цвет кнопки, в колонке, а остальным назначаем другой цвет
    :param keyboard: Клавиатура в которой идет замена.
    :param color_active: Новой цвет.
    :param color_disabled: Цвет остальным.
    :param settings: Текущие настройки клавиатуры
    :return:
    """
    for (
        button_name,
        row,
    ) in settings.get_rows.items():
        buttons = keyboard.keyboard.buttons.get(row)
        for button in buttons:
            if button.name == button_name:
                button.color = color_active
            else:
                button.color = color_disabled
