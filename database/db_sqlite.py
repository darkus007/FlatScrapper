"""
Модуль для работы с базой данных sqlite3.
"""

import sqlite3
from typing import Dict
import os

PATH = 'db'
DATABASE = 'db.sqlite3'

connect = sqlite3.connect(os.path.join(PATH, DATABASE))
cursor = connect.cursor()


def create_db() -> None:
    """
    Создает базу данных и таблицы в ней,
    если база и таблицы уже существуют,
    то ничего не делает.
    """
    with open('database/createdb.sql', 'r') as file:
        sql = file.read()
    cursor.executescript(sql)
    connect.commit()


def drop(*table_names: str) -> None:
    """ Очищает таблицы в базе данных. """
    for table in table_names:
        cursor.execute(f"DROP TABLE IF EXISTS {table}")
        connect.commit()


def insert(table: str, data: Dict) -> None:
    """
    Добавляет запись в базу данных.

    :param table: Название таблицы.
    :param data: Словарь для записи,
                где ключ - поле таблицы,
                а значение - данные для записи.
    :return: None.
    """
    columns = ', '.join(data.keys())
    values = [tuple(data.values())]
    placeholders = ", ".join("?" * len(data.keys()))
    cursor.executemany(
        f"INSERT INTO {table} "
        f"({columns}) "
        f"VALUES ({placeholders})",
        values)
    connect.commit()


def fetch(table: str, columns: list[str]) -> list[tuple | None]:
    """
    Возвращает результаты из одной таблицы базы данных.

    :param table: Название таблицы.
    :param columns: Список с полями таблицы.
    :return: Список кортежей.
    """
    columns_joined = ", ".join(columns)
    cursor.execute(f"SELECT {columns_joined} FROM {table}")
    return cursor.fetchall()


def execute_sql_fetch(sql: str) -> list[tuple | None]:
    """
    Выполняет sql запрос и возвращает результат.

    :param sql: SQL запрос.
    :return: Список кортежей или пустой список.
    """
    cursor.execute(sql)
    return cursor.fetchall()


def execute_sql(sql: str) -> None:
    """
    Выполняет sql команду.

    :param sql: SQL запрос.
    :return: None.
    """
    cursor.execute(sql)
    connect.commit()
