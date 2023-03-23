from copy import deepcopy
from bot.data_classes import MessageFromVK, KeyboardEventEnum, MessageFromKeyboard
from bot.vk.vk_keyboard.buttons import Button, Title
from bot.vk.vk_keyboard.data_classes import TypeColor
from bot.vk.vk_keyboard.keyboard import Keyboard as KeyboardSchema
from bot.workers.keyboard import Keyboard

base_structure = {
    0: [
        Title(
            name="Присоединится к игре",
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.keyboard = KeyboardSchema(name=self.name, buttons=deepcopy(base_structure), one_time=False)
        self.button_handler = {
            "Назад": self.button_back,
        }

    async def button_back(self, message: "MessageFromVK") -> "KeyboardEventEnum":
        """Вернуться в RootKeyboard"""
        from bot.vk.keyboards.root import RootKeyboard
        return await self.redirect(RootKeyboard, [message.user_id])

    async def event_update(self, message: MessageFromKeyboard):
        """В клавиатуре за которой мы наблюдаем произошли изменения, кто-то вышел, вошел"""
        self.logger.debug(f"UPDATE_EVENT {self.name} start...")
        # Сюда приходят данные от клавиатур за которыми идет слежка
        # обновляем данные по клавиатуре
        if keyboard := self.bot.get_keyboard_by_name(message.keyboard_name):
            if keyboard.users:
                if commander_user := self.bot.get_user_by_id(keyboard.users[0]):
                    self.data[keyboard.name] = commander_user.user_id
            else:
                self.logger.error(f"No users in the keyboard:  {message.keyboard_name}")
        else:
            self.logger.error(f"Keyboard not found: {message.keyboard_name}")
            self.data.pop(message.keyboard_name, None)
        self.logger.debug(f"UPDATE_EVENT {self.name} Complete,{message}")
        return KeyboardEventEnum.select

    async def event_delete(self, message: MessageFromKeyboard):
        self.bot.logger.warning(f"DELETE_EVENT {self.name} {message}")
        self.data.pop(message.keyboard_name, None)
        self.bot.logger.warning(f"DELETE_EVENT {self.name} complete")
        return KeyboardEventEnum.select

    async def update(self):
        """Обновление клавиатуры после получения изменений в результате обработки сообщения от Клавиатуры или User"""
        buttons = {0: deepcopy(base_structure[0])}
        self.button_handler = {"Назад": self.button_back}
        index = 0
        for keyboard_name in self.data.copy():
            is_error = True
            if keyboard := self.bot.get_keyboard_by_name(keyboard_name):
                if users := keyboard.users.copy():
                    if user := self.bot.get_user_by_id(users[0]):
                        total = keyboard.get_setting_keyboard().players.value
                        button = Button(
                            name=keyboard_name,
                            label=f"{user.name} {len(users)} из {total}",
                            color=TypeColor.blue,
                        )
                        index += 1
                        is_error = False
                        buttons[index] = [button]
                        self.button_handler[keyboard_name] = self.button_join_command
                    else:
                        self.logger.error(f"No users in the keyboard: {keyboard_name}")
                else:
                    self.logger.error(f"No users in the keyboard:  {keyboard_name}")
            else:
                self.logger.error(f"Keyboard not found: {keyboard_name}")
            if is_error:
                self.data.pop(keyboard_name)
        buttons[len(buttons)] = deepcopy(base_structure[1])
        self.keyboard.buttons = buttons

    async def button_join_command(self, message: "MessageFromVK") -> "KeyboardEventEnum":
        if team_keyboard_server := self.bot.get_keyboard_by_name(message.payload.button_name):
            user_name = self.get_user(message.user_id).name
            return await self.redirect(team_keyboard_server, [message.user_id],
                                       body=f"Присоединился к команде {user_name}")
        else:
            self.logger.warning("Team command keyboard is not available")
            # можем переправить на страничку, что типа извини команды набран,
            # а или была расформирована пока ты кликал мышку
        return KeyboardEventEnum.select
