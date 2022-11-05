"""
Модуль содержит класс который, пропускает сообщения
только от аутентифицированных пользователей.
"""
from aiogram import types
from aiogram.dispatcher.handler import CancelHandler
from aiogram.dispatcher.middlewares import BaseMiddleware
from typing import Iterable


class AccessMiddleware(BaseMiddleware):
    def __init__(self, access_id: Iterable[int]):
        """
        Аутентификация — пропускаем сообщения только от авторизованных пользователей.

        :param access_id: id пользователей, которым будет открыт доступ.
        """
        self.access_id = access_id
        super().__init__()

    async def on_process_message(self, message: types.Message, _):
        if int(message.from_user.id) not in self.access_id:
            await message.answer("Access Denied.")
            raise CancelHandler()
