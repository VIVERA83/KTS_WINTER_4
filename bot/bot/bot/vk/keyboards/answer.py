from copy import deepcopy
from typing import Optional

from bot.data_classes import KeyboardEventEnum, MessageFromVK, MessageFromKeyboard
from bot.vk.keyboards.data_classes import TimeoutKeyboard, GameData
from bot.vk.keyboards.round_result import RoundResultKeyboard
from bot.vk.vk_keyboard.buttons import Button, Title
from bot.vk.vk_keyboard.data_classes import TypeColor
from bot.vk.vk_keyboard.keyboard import Keyboard as KeyboardSchema
from bot.workers.keyboard import Keyboard

base_structure = {
    0: [
        Title(
            name="Ваш ответ?",
            label="Ваш ответ?",
            color=TypeColor.white,
            help_string="Выберите ответ, либо предложите свой. Напишете",
        )
    ],
    1: [
        Title(
            name="Вариант ответа",
            label="Вариант ответа",
            color=TypeColor.white,
            help_string="Вариант ответа, на выбор",
        ),
        Title(
            name="Голосов в поддержку",
            label="Голосов в поддержку",
            color=TypeColor.white,
            help_string="Количество участников которые придерживают предложенный вариант",
        ),
    ],
}


class AnswerKeyboard(Keyboard):
    name = "AnswerKeyboard"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.keyboard = KeyboardSchema(
            name="AnswerKeyboard", buttons=base_structure, one_time=False
        )
        self.settings: Optional["GameData"] = None
        self.timeout_keyboard = TimeoutKeyboard(
            keyboard=RoundResultKeyboard,
            user_ids=deepcopy(self.users),
            is_private=True,
        )

    async def event_new(self, message: MessageFromKeyboard) -> KeyboardEventEnum:
        await self.first_run_keyboard(message)
        return KeyboardEventEnum.update

    async def first_run_keyboard(self, message: MessageFromKeyboard):
        if self.is_first:
            if self.users:
                self.is_first = False
                self.settings = await self.get_keyboard_default_setting()
                self.create_buttons()
                self.settings.watcher += 1
            else:
                self.logger.error(f"The list of users is empty: {self.users}")

    async def get_keyboard_default_setting(self) -> "GameData":
        """Достать настройки игры из пользователя из первого"""
        from bot.vk.keyboards.round_game import RoundGameKeyboard

        return self.get_user(self.users[0]).get_setting_keyboard(RoundGameKeyboard.name)

    def create_buttons(self):
        """Создаем кнопки"""
        buttons = {0: deepcopy(base_structure[0])}
        for key, user_id in enumerate(self.settings.round.users, 2):
            if f"{self.settings.round.answers[f'{user_id}a'].value}" != "Нет ответа":
                buttons[1] = deepcopy(base_structure[1])
                button_answer = Button(
                    name=f"{user_id}a",
                    label=f"{self.settings.round.answers[f'{user_id}a'].value}",
                    color=TypeColor.blue,
                )
                # вычитываем кол-во голосов за данный ответ
                sum_vote = sum(self.settings.round.votes[f"{user_id}v"].value.values())
                help_string = f"За проголосовали: {sum_vote} участник(а)"
                button_vote = Title(
                    name=f"{user_id}v",
                    label=f"{sum_vote}",
                    color=TypeColor.white,
                    help_string=help_string,
                )

                buttons[key] = [button_answer, button_vote]
                self.button_handler[f"{user_id}a"] = self.button_answer
                self.button_handler[f"{user_id}v"] = self.button_vote
        self.keyboard.buttons = buttons

    async def button_vote(self, message: MessageFromVK) -> KeyboardEventEnum:
        """Формируем ответ на нажатие event button"""
        message.event_data = self.keyboard.get_help_string_from_title(
            message.payload.button_name
        )
        return KeyboardEventEnum.select

    async def button_answer(self, message: MessageFromVK) -> KeyboardEventEnum:
        """Выбор ответа из имеющихся вариантов, и переход в клавиатуру с результатом раунда"""
        from bot.vk.keyboards.round_result import RoundResultKeyboard

        if user_data := self.settings.round.users.get(f"{message.user_id}"):
            if user_data.value:
                if message.body == self.settings.question.correct_answer:
                    self.settings.experts += 1
                    self.settings.watcher -= 1
                return await self.redirect(
                    RoundResultKeyboard,
                    deepcopy(self.users),
                    is_private=True,
                    kill_parent=True,
                    body=f"{self.get_user(message.user_id).name} : Ваш ответ {message.body}"
                )
        else:
            message.body = f"{self.get_user(message.user_id).name}: Отвечать назначен другой участник команды"
        return KeyboardEventEnum.select

    async def text_all(self, message: MessageFromVK) -> KeyboardEventEnum:
        """Текст переданный в сообщение сохраняем в настройках и присваиваем кнопке"""
        from bot.vk.keyboards.round_result import RoundResultKeyboard

        if user_data := self.settings.round.users.get(f"{message.user_id}"):
            if user_data.value:
                self.settings.round.answer = message.body
                if message.body == self.settings.question.correct_answer:
                    self.settings.experts += 1
                    self.settings.watcher -= 1
                return await self.redirect(
                    RoundResultKeyboard,
                    deepcopy(self.users),
                    is_private=True,
                    kill_parent=True,
                    body=f"{self.get_user(message.user_id).name} : Ваш ответ {message.body}"
                )
        else:
            message.body = f"{self.get_user(message.user_id).name}: Отвечать назначен другой участник команды"
        return KeyboardEventEnum.select
