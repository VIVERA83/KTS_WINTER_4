from copy import deepcopy
from typing import Union, Optional

from bot.data_classes import MessageFromVK, MessageFromKeyboard, KeyboardEventEnum
from bot.vk.keyboards.connect_team_failed import ConnectTeamFailed
from bot.vk.keyboards.data_classes import GameSessionSettings
from bot.vk.keyboards.game_session_settings import GameSessionSettingKeyboard
from bot.vk.keyboards.team_is_ready import TeamIsReadyKeyboard
from bot.vk.vk_keyboard.buttons import Button, Title
from bot.vk.vk_keyboard.data_classes import TypeColor
from bot.vk.vk_keyboard.keyboard import Keyboard as KeyboardSchema
from bot.workers.keyboard import Keyboard

base_structure = {
    0: [
        Title(
            name="Состав команды",
            label="Состав команды",
            color=TypeColor.white,
            help_string="Это Ваша команда, когда она будет собрана игра начнется",
        )
    ],
    1: [
        Button(
            name="Выйти",
            label="Выйти",
            color=TypeColor.red,
        )
    ],
}


class TeamServerKeyboard(Keyboard):
    name = "TeamServerKeyboard"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.farewell_text = f"Команда расформирована"
        self.keyboard = KeyboardSchema(
            name=self.name, buttons=deepcopy(base_structure), one_time=False
        )
        self.settings: Optional[GameSessionSettings] = None

    async def button_back(self, message: MessageFromVK) -> KeyboardEventEnum:
        from bot.vk.keyboards.join_game import JoinGameKeyboard
        from bot.vk.keyboards.team_disbanded import TeamDisbandedKeyboard
        from bot.vk.keyboards.game_session_settings import GameSessionSettingKeyboard

        # Если это создатель сервера и он не один, команда распускается.
        user = self.get_user(message.user_id)
        if len(self.users) > 1 and user.user_id == self.users[0]:
            users = []
            for user_id in self.users:
                if user := self.get_user(user_id):
                    users.append(user.user_id)
            await self.redirect(
                TeamDisbandedKeyboard,
                users,
                body=f"Команда распушена по инициативе организатора: {user.name}",
            )
            # обычный пользователь переходит в JoinGameKeyboard
            return KeyboardEventEnum.delete
        elif message.user_id != self.users[0]:
            await self.redirect(JoinGameKeyboard, [message.user_id], is_dynamic=True)
            return KeyboardEventEnum.update
        else:
            # Если в команде только организатор, переносим игрока, и обнуляем слушателей
            await self.redirect(
                GameSessionSettingKeyboard,
                [message.user_id],
                is_dynamic=True,
                is_private=True,
            )
            return KeyboardEventEnum.delete

    async def update(self):
        await self.update_buttons()

    async def event_new(self, message: MessageFromKeyboard) -> KeyboardEventEnum:
        self.settings = await self.get_setting_keyboard()
        # если количество пользователей ровное для начала игры
        if self.settings.players.value == len(self.users):
            # ИГРОВОЕ МЕНЮ СТАРТ ОСОБОЕ МЕНЮ
            await self.redirect(
                TeamIsReadyKeyboard,
                deepcopy(self.users),
                is_private=True,
                is_dynamic=True,
            )
            return KeyboardEventEnum.delete

        # connect_to_team_failed
        # если пользователей больше чем надо, убираем лишних
        elif self.settings.players.value < len(self.users):
            count_delete = len(self.users) - self.settings.players.value
            list_delete = [self.users.pop(-1) for _ in range(count_delete)]
            # отправляем users которые не вышли за рамки максимального кол-ва участников в следующие keyboard
            await self.redirect(
                TeamIsReadyKeyboard,
                deepcopy(self.users),
                is_private=True,
                is_dynamic=True,
            )
            # остальных отправляем в keyboard которая говорит что не успели.
            await self.redirect(ConnectTeamFailed, list_delete)
            return KeyboardEventEnum.delete
        # ну а если нужного кол-ва не набралось продолжаем ждать
        return KeyboardEventEnum.update

    async def get_keyboard_default_setting(self) -> Union["GameSessionSettings"]:
        """Настройки клавиатуры по умолчанию, место куда скидывают настройки по умолчанию для клавиатур"""
        return self.get_user(self.users[0]).get_setting_keyboard(
            GameSessionSettingKeyboard.name
        )

    async def update_buttons(self):
        buttons = {0: deepcopy(base_structure[0])}
        self.button_handler = {"Выйти": self.button_back}
        for key, user_id in enumerate(self.users, 1):
            user = self.get_user(user_id)
            button = Title(
                name=str(user_id),
                label=user.name,
                color=TypeColor.blue,
                help_string="Тут можно получить информацию по пользователю",
            )
            buttons[key] = [button]
        buttons[len(buttons)] = deepcopy(base_structure[1])
        self.keyboard.buttons = buttons
