"""
Телеграм бот.
Возвращает информацию из базы данных по запросу пользователя.

Поддерживаемые команды (параметры вводятся через пробел):
ЖК - для получения списка доступных ЖК.
Город - для получения списка доступных городов.
Квартиры "Название города" или "%" для выбора всех городов
        "Название ЖК или %" "Количество комнат" "Максимальная цена"
        "Год заселения" "Отделка (0 или 1)" "Бронь (active или %)".
        Например: Квартиры %Москв% % 1 10000000 2024 1 active.
Квартира id - для получения информации по выбранной квартире, включая статистику изменения цены
        (id квартиры можно узнать из предыдущей команды "Квартиры ...").
"""

import os
import logging

from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor

from settings import LOGGER_LEVEL
import services.logger

from .middlewares import AccessMiddleware
from .commands import parse_command


bot_logger = services.logger.init_logger(__name__, LOGGER_LEVEL)
logging.getLogger('urllib3').setLevel(logging.ERROR)

bot = Bot(token=os.getenv('R2D2_BOT_TOKEN'))
dp = Dispatcher(bot)                                # handler
dp.middleware.setup(AccessMiddleware((int(os.getenv('ACCESS_ID')), )))  # фильтр по токену tulpe[int]

hello_msg = """<b>Привет!</b>\n<b>Набери:</b>\n<b>квартира</b> "id" - для получения статистики по выбранной квартире;
<b>квартиры</b> "Город или %" "Название ЖК или %" "Количество комнат" "Максимальная цена" "Год заселения" "Отделка (0 или 1)" "Бронь (active или %)"
Например: <i>Квартиры %Москв% % 1 10000000 2024 1 active</i>
<b>Город</b> - для получения списка доступных городов;
<b>ЖК</b> - для получения списка доступных ЖК."""


@dp.message_handler(commands=['start', 'help', 'Start', 'Help'])
async def start_command(message: types.Message):
    await message.answer(hello_msg, parse_mode=types.ParseMode.HTML)


@dp.message_handler()
async def execute_the_command(message: types.Message):
    command = message.text.split(" ")
    bot_logger.info(f"{message.from_user.id}: {command}")

    answer = parse_command(command)
    if isinstance(answer, str):
        await message.answer(parse_command(command))
    elif isinstance(answer, tuple):
        if answer[0] == 'send_file':
            with open(answer[1] + '.xlsx', 'rb') as file:
                await bot.send_document(message.chat.id, document=file)
                os.remove(answer[1] + '.xlsx')
        elif answer[0] == 'unknown command':
            await message.answer("<b>Команда не распознана.</b>\n" + hello_msg,
                                 parse_mode=types.ParseMode.HTML)


def run():
    """Запускает телеграм бота. """
    executor.start_polling(dp)


if __name__ == '__main__':
    run()
