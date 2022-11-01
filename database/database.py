"""
Модуль для работы с базой данных sqlite
"""

import sqlite3
from functools import wraps
from typing import TypeVar, Callable

from services import *


DATABASE_PATH = '../db/db.sqlite3'

callable_func = TypeVar("callable_func", bound=Callable)


def create_db():
    """ Создает базу данных и таблицы в ней """
    with open('createdb.sql', 'r') as file:
        sql = file.read()
    with sqlite3.connect(DATABASE_PATH) as conn:
        cur = conn.cursor()
        cur.executescript(sql)


def drop_tablets(*args):
    with sqlite3.connect(DATABASE_PATH) as conn:
        cur = conn.cursor()
        for arg in args:
            cur.execute(f"DROP TABLE IF EXISTS {arg}")


def db_insert(func: Callable) -> callable_func:
    """
    Декоратор для записи в базу данных.
    В случае ошибок, возвращает базу данных в исходное состояние до начала записи.

    :param func: Функция, которая содержит команду cur.execute("SQL команда")
    :return: None
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cur = conn.cursor()

            func(cur, *args, **kwargs)

            conn.commit()

        except sqlite3.Error as er:
            if conn:
                conn.rollback()
            print(f"Ошибка записи в базу данных {er}.")
        finally:
            if conn:
                conn.close()

    return wrapper


@db_insert
def insert_project(cur, data: json, date_time: str) -> None:
    """
    Добавляет в базу данных запись об одном ЖК.

    :param data: Данные для записи в формате json {"name": ..., "sub_name": ..., ...}.
    :param date_timeЖ Время сбора данные (когда данные были получены с сайта).
    """
    cur.execute("""INSERT INTO projects (project_id, city, name, url, metro, time_to_metro, 
                latitude, longitude, address, data_created)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (data['id'], "Москва", data['name'], data['url'], data['metro'], data['time_to_metro'],
                 data['longitude'], data['latitude'], "Address", date_time))


@db_insert
def insert_flat(cur, project_id, flat: json, date_time: str) -> None:
    """
    Добавляет в базу данных запись об одной квартире.

    :param data: Данные для записи в формате json {"name": ..., "sub_name": ..., ...}.
    :param date_timeЖ Время сбора данные (когда данные были получены с сайта).
    """
    cur.execute("""INSERT INTO flats (flat_id, project_id, address, floor, rooms, 
                area, finishing, bulk, settlement_date, url_suffix, data_created)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (flat['flat_id'], project_id, flat['address'], flat['floor'], flat['rooms'],
                 flat['area'], flat['finishing'], flat['bulk'], flat["settlement_date"],
                 flat["url_suffix"], date_time))


@db_insert
def insert_price(cur, flat: json, date_time: str) -> None:
    """
    Добавляет в базу данных запись об одной квартире.

    :param data: Данные для записи в формате json {"name": ..., "sub_name": ..., ...}.
    :param date_timeЖ Время сбора данные (когда данные были получены с сайта).
    """
    cur.execute("""INSERT INTO prices (price_id, benefit_name, benefit_description, 
                price, meter_price, booking_status, data_created)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (flat['flat_id'], flat['benefit_name'], flat['benefit_description'],
                 flat['price'], flat['meter_price'], flat['booking_status'], date_time))


if __name__ == '__main__':
    create_db()
    # drop_tablets('projects', 'flats', 'prices')
    data = read_json_from_file("../temp/all_flat_info.json")
    data_time = get_data_time('%Y-%m-%d')
    for d in data:
        insert_project(d, data_time)
        for f in d['flats']:
            insert_flat(project_id=d['id'], flat=f, date_time=data_time)
            insert_price(flat=f, date_time=data_time)
    pass
