"""
Модуль для работы с выбранной базой данных.
В текущей реализации sqlite3.
"""

import dataclasses

from .db_sqlite import *
from services import read_json_from_file, Project, Flat, Price


def save_to_database(table_name: str, data_to_save: list[Project | Flat | Price]) -> None:
    """
    Сохраняет данные в базу данных.

    :param table_name: Название таблицы в базе данных.
    :param data_to_save: Данные для сохранения в виде списка словарей {'название поля': значение}.
    :return: None.
    """
    for data in data_to_save:
        try:
            insert(table_name, dataclasses.asdict(data))
        except sqlite3.IntegrityError:
            # такая запись уже имеется,
            # отсеиваем ЖК и квартиры по уникальным project_id и flat_id
            # при этом цены уникального поля не имеют и будут записаны все
            # дубликаты с ценой удалим вызвав функцию "db_sqlite.remove_duplicates_prices_table()"
            pass


if __name__ == '__main__':
    create()
    # drop('projects', 'flats', 'prices')
    # data = read_json_from_file("../temp/all_projects.json")
    # save_to_database('projects', data)
    # data = read_json_from_file("../temp/all_flats.json")
    # save_to_database('flats', data)
    # data = read_json_from_file("../temp/all_prices.json")
    # save_to_database('prices', data)
    # remove_duplicates_prices_table()
