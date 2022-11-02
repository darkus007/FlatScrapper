"""
Модуль для работы с базой данных sqlite.
"""

import sqlite3
from typing import Dict
import os

PATH = 'db'
DATABASE = 'db.sqlite3'


def create() -> None:
    """
    Создает базу данных и таблицы в ней,
    если база и таблицы уже существуют,
    то ничего не делает.
    """
    with open('database/createdb.sql', 'r') as file:
        sql = file.read()
    with sqlite3.connect(os.path.join(PATH, DATABASE)) as conn:
        cur = conn.cursor()
        cur.executescript(sql)


def drop(*table_names: str) -> None:
    """ Очищает таблицы в базе данных. """
    with sqlite3.connect(os.path.join(PATH, DATABASE)) as conn:
        cur = conn.cursor()
        for table in table_names:
            cur.execute(f"DROP TABLE IF EXISTS {table}")


def insert(table: str, data: Dict) -> None:
    """ Добавляет запись в базу данных. """
    columns = ', '.join(data.keys())
    values = [tuple(data.values())]
    placeholders = ", ".join("?" * len(data.keys()))
    with sqlite3.connect(os.path.join(PATH, DATABASE)) as conn:
        cur = conn.cursor()
        cur.executemany(
            f"INSERT INTO {table} "
            f"({columns}) "
            f"VALUES ({placeholders})",
            values)


def remove_duplicates_prices_table():
    """
    Удаляет одинаковые цены из таблицы prices
    (если цена не изменилась, равна предыдущей
    цене и не изменился статус бронирования, то
    такая запись будет удалена).
    """
    with sqlite3.connect(os.path.join(PATH, DATABASE)) as conn:
        cur = conn.cursor()
        cur.execute("""DELETE FROM prices WHERE rowid NOT IN 
                    (SELECT min(rowid) FROM prices GROUP BY price_id, price, booking_status)""")
