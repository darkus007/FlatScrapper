"""
Модуль содержит служебные функции,
которые помогают в отладке при написании парсера
и/или разгружают основной код.
"""

import json


def read_from_file(file_name: str) -> str:
    """ Читает данные из файла. """
    with open(file_name, 'r') as file:
        return file.read()


def write_to_file(file_name: str, data: str) -> None:
    """ Пишет данные в файл. """
    with open(file_name, 'w') as file:
        file.write(data)


def write_json_to_file(file_name: str, data: json) -> None:
    """
    Пишет json в файл.
    Вспомогательная функция для написания парсера.
    :param file_name: Название файла,
                      расширение ".json" будет добавлено автоматически.
    :param data: Данные для записи в формате json.
    """
    with open(file_name + ".json", 'w') as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


def read_json_from_file(file_name: str) -> json:
    """
    Читает json из файла.
    Вспомогательная функция для написания парсера.
    :param file_name: Название файла с расширением.
    :param data: Данные для записи в формате json.
    """
    with open(file_name, 'r') as file:
        return json.load(file)