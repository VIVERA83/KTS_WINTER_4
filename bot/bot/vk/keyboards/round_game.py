from copy import deepcopy
from random import randint
from typing import Optional

from icecream import ic

from bot.data_classes import KeyboardEventEnum, MessageFromVK, MessageFromKeyboard
from bot.vk.keyboards.answer import AnswerKeyboard
from bot.vk.keyboards.data_classes import Round, Data, TimeoutKeyboard
from bot.vk.keyboards.game_session_settings import GameSessionSettingKeyboard
from bot.vk.vk_keyboard.buttons import Button, Title
from bot.vk.vk_keyboard.data_classes import TypeColor
from bot.vk.vk_keyboard.keyboard import Keyboard as KeyboardSchema
from bot.workers.keyboard import Keyboard

base_structure = {
    0: [
        Title(
            name="Round",
            label="Round",
            color=TypeColor.white,
            help_string="Привет, отсюда начинается работа с ботом",
        )
    ],
    1: [
        Title(
            name="Вопрос",
            label="Вопрос",
            color=TypeColor.blue,
            help_string="Первый в вписке это командир"
        ),
    ],
    2: [
        Title(
            name="Участник",
            label="Участник",
            color=TypeColor.white,
            help_string="Первый капитан, зеленый - участник который будет отвечать, его назначает капитан"
        ),
        Title(
            name="Вариант ответа",
            label="Вариант ответа",
            color=TypeColor.white,
            help_string="Вариант ответа, на выбор"
        ),
        Title(
            name="Голосов в поддержку",
            label="Голосов в поддержку",
            color=TypeColor.white,
            help_string="Количество участников которые придерживают предложенный вариант"
        ),

    ],
    3: [
        Button(
            name="Досрочный ответ",
            label="Досрочный ответ",
            color=TypeColor.green,
        ),
    ],
}


class RoundGameKeyboard(Keyboard):
    name = "RoundGameKeyboard"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.keyboard = KeyboardSchema(name="RootKeyboard", buttons=base_structure, one_time=False)
        self.timeout_keyboard = TimeoutKeyboard(keyboard=AnswerKeyboard,
                                                user_ids=deepcopy(self.users),
                                                is_private=True,
                                                )

    async def event_new(self, message: MessageFromKeyboard) -> KeyboardEventEnum:
        await self.first_run_keyboard(message)
        return KeyboardEventEnum.update

    async def update(self):
        for buttons in self.keyboard.buttons.values():
            for button in buttons:
                # обновляем Участников
                if data := self.data["settings"].users.get(button.name):
                    if data.value:
                        button.color = TypeColor.green
                    else:
                        button.color = TypeColor.blue
                # обновляем голоса
                elif data := self.data["settings"].votes.get(button.name):
                    button.label = f"{sum(data.value.values())}"

    async def first_run_keyboard(self, message: MessageFromKeyboard):
        if self.is_first:
            if self.users:
                self.is_first = False
                self.data["settings"] = self.get_keyboard_default_setting()
                self.data["settings"].number += 1
                question = await self.bot.get_random_question()
                self.data["settings"].id = question.get("id")
                self.data["settings"].question = question.get("title")
                self.data["settings"].correct_answer = question.get("correct_answer")
                self.create_buttons()
                # Создаем игровую сессию в БД
                if not self.data["settings"].game_session_id:
                    data = {"captain_id": self.users[0],
                            "users": self.users,
                            }
                    self.data["settings"].game_session_id = (await self.bot.create_game_session(data)).get("id")
            else:
                self.logger.error(f"The list of users is empty: {self.users}")

    async def button_set_responding(self, message: "MessageFromVK") -> "KeyboardEventEnum":
        """Назначить отвечающего на вопрос"""
        if message.user_id == self.users[0]:
            for user_data in self.data["settings"].users.values():
                if message.payload.button_name == user_data.button_name:
                    user_data.value = True
                else:
                    user_data.value = False
            message.body = f"{self.get_user(message.user_id).name}: Назначил нового отвечающего"
            return KeyboardEventEnum.update
        else:
            message.body = f"{self.get_user(message.user_id).name}: Отвечающего на вопрос может " \
                           f"назначить только капитан команды"
            return KeyboardEventEnum.select

    async def button_set_vote(self, message: "MessageFromVK") -> "KeyboardEventEnum":
        """Передаем свой голос понравившемуся ответу"""
        try:
            for vote in self.data["settings"].votes.values():
                if vote.button_name == message.payload.button_name:
                    if vote.value.get(message.user_id) == 1:
                        vote.value[message.user_id] = 0
                    else:
                        vote.value[message.user_id] = 1
                else:
                    vote.value[message.user_id] = 0
        except Exception as e:
            ic(e)
        return KeyboardEventEnum.update

    async def button_answer(self, message: "MessageFromVK") -> "KeyboardEventEnum":  # noqa
        from bot.vk.keyboards.answer import AnswerKeyboard
        if user_data := self.data["settings"].users.get(f"{message.user_id}"):
            if user_data.value:
                return await self.redirect(AnswerKeyboard, deepcopy(self.users), is_private=True, kill_parent=self.name)
            else:
                message.body = f"{self.get_user(message.user_id).name}: Отвечать назначен другой участник команды"
        return KeyboardEventEnum.select

    async def text_all(self, message: MessageFromVK) -> KeyboardEventEnum:
        """Текст переданный в сообщение сохраняем в настройках и присваиваем кнопке"""
        for buttons in self.keyboard.buttons.values():
            for button in buttons:
                if button.name == f"{message.user_id}a":
                    button.label = message.body
                    if answer := self.data["settings"].answers.get(f"{message.user_id}a"):
                        answer.value = message.body
                    break
        message.body = f"{self.get_user(message.user_id).name} : {message.body}"
        return KeyboardEventEnum.update

    def get_keyboard_default_setting(self) -> "Round":
        """Достать настройки игры из пользователя из первого, тот кто создал игровую сессию"""
        try:
            self.data["settings"] = self.get_user(self.users[0]).get_setting_keyboard(self.__class__.name)
            if not self.data.get("settings"):
                self.data["settings"] = Round()
                self.data["settings"].session_setting = self.get_user(self.users[0]).get_setting_keyboard(
                    GameSessionSettingKeyboard.name)
                # Назначаем случайного капитана команды
                if self.data["settings"].number == 0:
                    self.choose_random_captain()
        except Exception as e:
            ic(e)
        # Значение кнопок по умолчанию
        try:
            for key, user_id in enumerate(self.users, 3):
                self.data["settings"].users[f"{user_id}"] = Data(value=True if key == 3 else False, row=key,
                                                                 button_name=f"{user_id}")
                self.data["settings"].answers[f"{user_id}a"] = Data(value="Нет ответа", row=key,
                                                                    button_name=f"{user_id}a")
                self.data["settings"].votes[f"{user_id}v"] = Data(value={}, row=key, button_name=f"{user_id}v")
                user = self.get_user(user_id)
                user.set_setting_keyboard(self.__class__.name, self.data["settings"])
        except Exception as e:
            ic(e)
        return self.data["settings"]

    def choose_random_captain(self):
        """Выбираем капитана"""
        if not self.data["settings"].capitan:
            self.users.insert(0, self.users.pop(randint(0, len(self.users) - 1)))
            self.data["settings"].capitan = deepcopy(self.users[0])

    def create_buttons(self):
        """Создаем кнопки с участниками игры"""
        try:
            buttons = deepcopy(base_structure)
            buttons[1][0].label = self.data['settings'].question
            buttons[1][0].help_string = self.data['settings'].question
            self.button_handler = {
                "Досрочный ответ": self.button_answer
            }
            for key, user_id in enumerate(self.users, 3):
                user = self.get_user(user_id)
                button_user = Button(
                    name=f"{user_id}",
                    label=user.name,
                    color=TypeColor.white,
                )
                button_answer = Button(
                    name=f"{user_id}a",
                    label="Нет ответа",
                    color=TypeColor.blue,
                )
                button_vote = Button(
                    name=f"{user_id}v",
                    label="0",
                    color=TypeColor.blue,
                )
                buttons[key] = [button_user, button_answer, button_vote]
                self.button_handler[f"{user_id}"] = self.button_set_responding
                self.button_handler[f"{user_id}v"] = self.button_set_vote
            buttons[len(buttons)] = deepcopy(base_structure[len(base_structure) - 1])
            buttons[0][0].label = f"{buttons[0][0].label} {self.data['settings'].number}"
            buttons[0][
                0].help_string = f"Текущий раунд {self.data['settings'].number} из {self.data['settings'].session_setting.rounds.value}"
            self.keyboard.buttons = buttons
        except Exception as e:
            self.logger.critical(e.args)
        ic("Settings ok")
