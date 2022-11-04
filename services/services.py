"""
Модуль содержит служебные функции,
которые помогают в отладке при написании парсера
и/или разгружают основной код.
"""

import json
import xlsxwriter
from datetime import datetime
from typing import Any, Union

from .data_classes import JsonDataclassEncoder


def get_value_from_json(json_data: Union[list, dict], keys: list) -> Any:
    """
    Возвращает данные из json по переданным ключам.
    Обрабатывает отсутствие ключа в dict и IndexError для list, в этом случае возвращает None.

    :param json_data: Json из которого требуется получить значение.
    :param keys: Список ключей, по которым лежит значение.
    :return: Любые данные, обычно str, int, float, None, ...
    """
    if len(keys) == 1:
        if isinstance(json_data, dict):
            return json_data.get(keys[0], None)
        elif isinstance(json_data, list):
            try:
                return json_data[keys[0]]
            except IndexError:
                return None
            except TypeError:
                return None
    else:
        key = keys.pop(0)
        if isinstance(json_data, dict):
            return get_value_from_json(json_data.get(key, None), keys)
        elif isinstance(json_data, list):
            try:
                return get_value_from_json(json_data[key], keys)
            except IndexError:
                return None


def save_to_excel_file(data: list[tuple], file_name: str) -> None:
    """
    Сохраняет полученную из базы данных информацию в excel таблицу.

    :param data: Информация из базы данных.
    :param file_name: Путь и имя excel файла (расширение будет добавлено автоматически).
    :return: None.
    """
    head = ('id', 'ЖК', 'Город', 'Адрес', 'Корпус', 'Количество комнат', 'Площадь', 'Этаж', 'Отделка', 'Заселение',
            'Цена', 'Цена за метр', 'Бронь', 'Дата изменения цены', 'Ценовое предложение', 'Описание предложения',
            'Ссылка')

    # Создает Excel file и добавляет лист (worksheet).
    workbook = xlsxwriter.Workbook(file_name + '.xlsx')
    worksheet = workbook.add_worksheet()

    # Добавляем формат шрифта для выделения заголовка таблицы
    bold = workbook.add_format({'bold': True})
    # Пишем заголовок в 0 ряд с 0 позиции жирным шрифтом
    worksheet.write_row(0, 0, head, bold)

    # Пишем остальные данные обычным шрифтом
    row = 1
    for item in data:
        worksheet.write_row(row, 0, item)
        row += 1
    workbook.close()


def get_data_time(fmt: str = '%Y_%m_%d__%H_%M_%S') -> str:
    """
    Возвращает текущую дату и время.

    :param fmt: Формат даты и времени, по умолчанию '%Y_%m_%d__%H_%M_%S'.
    :return: Текущая дата (и время) в указанном формате.
    """
    return datetime.now().strftime(fmt)


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
    :param file_name: Название файла, расширение
                        ".json" будет добавлено
                        автоматически.
    :param data: Данные для записи в формате json.
    """
    with open(file_name + ".json", 'w') as file:
        json.dump(data, file, indent=4, ensure_ascii=False, cls=JsonDataclassEncoder)


def read_json_from_file(file_name: str) -> json:
    """
    Читает json из файла.
    :param file_name: Название файла включая расширение.
    :return: Данные в формате json.
    """
    with open(file_name, 'r') as file:
        return json.load(file)


if __name__ == '__main__':
    mdict = read_json_from_file("../temp/all_flat_info.json")
    print(get_value_from_json(mdict, [0, 'flats', 0, 'price']))
    print(mdict[0]['flats'][0]['price'])
