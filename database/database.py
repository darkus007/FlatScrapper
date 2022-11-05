"""
Модуль для работы с выбранной базой данных.
В текущей реализации sqlite3.
"""

import dataclasses

from .db_sqlite import *
from services import Project, Flat, Price, init_logger
from settings import LOGGER_LEVEL

logger = init_logger(__name__, LOGGER_LEVEL)

flats_filter = {'city': '%Москв%',
                'name': '%',
                'rooms': 1,
                'max_price': 10000000,
                'max_settlement_date': '2024-__-__',
                'finishing': True,
                'booking_status': 'active'
                }


def save_to_database(table_name: str, data_to_save: list[Project | Flat | Price]) -> None:
    """
    Сохраняет данные в базу данных.

    :param table_name: Название таблицы в базе данных.
    :param data_to_save: Данные для сохранения в виде списка словарей {'название поля': значение}.
    :return: None.
    """
    create_db()
    for data in data_to_save:
        try:
            insert(table_name, dataclasses.asdict(data))
        except sqlite3.IntegrityError:
            # такая запись уже имеется,
            # отсеиваем ЖК и квартиры по уникальным project_id и flat_id
            # при этом цены уникального поля не имеют и будут записаны все
            # дубликаты с ценой удалим вызвав функцию "db_sqlite.remove_duplicates_prices_table()"
            pass
        except Exception as ex:
            logger.error(f"Ошибка при сохранении в базу данных {ex}")


def get_flat(flat_id: int) -> list[tuple | None]:
    """
    Возвращает информацию по квартире из БД по id номеру.

    :param flat_id: id квартиры (значение поля flat_id в базе данных).
    :return: Список кортежей или пустой список.
    """
    sql_request = f"SELECT flat_id, name, city, flats.address, bulk, rooms, area, floor, finishing, settlement_date,\
                        price, meter_price, booking_status, prices.data_created, benefit_name, benefit_description, " \
                        f"url || url_suffix AS url_address \
                    FROM flats \
                    JOIN projects ON flats.project_id = projects.project_id \
                    JOIN prices ON flats.flat_id = prices.price_id " \
                              + f"WHERE flats.flat_id = {flat_id} ORDER BY prices.data_created"
    return execute_sql_fetch(sql_request)


def get_flats_by_filter(flats_filter: dict) -> list[tuple | None]:
    """ Возвращает все данные (включая историю изменения цены) по квартирам из БД по заданному фильтру. """

    sql_request = 'SELECT flat_id, name, city, flats.address, bulk, rooms, area, floor, finishing, settlement_date,\
                        price, meter_price, booking_status, prices.data_created, benefit_name, benefit_description, ' \
                        'url || url_suffix AS url_address \
                  FROM flats \
                  JOIN projects ON flats.project_id = projects.project_id \
                  JOIN prices ON flats.flat_id = prices.price_id ' \
                  f'WHERE city LIKE "{flats_filter["city"]}" ' \
                      f'AND name LIKE "{flats_filter["name"]}" ' \
                      f'AND rooms = {flats_filter["rooms"]} ' \
                      f'AND price <= {flats_filter["max_price"]} ' \
                      f'AND settlement_date <= "{flats_filter["max_settlement_date"]}" ' \
                      f'AND finishing = {flats_filter["finishing"]} ' \
                      f'AND booking_status LIKE "{flats_filter["booking_status"]}" ' \
                  "ORDER BY price"
    return execute_sql_fetch(sql_request)


def get_flats_by_filter_last_price(flats_filter: dict) -> list[tuple | None]:
    """ Возвращает актуальные (текущие) данные по квартирам из БД по заданному фильтру """
    sql_request = 'SELECT * FROM ' \
                  '(SELECT flat_id, name, city, flats.address, bulk, rooms, area, floor, finishing, settlement_date,\
                            price, meter_price, booking_status, max(prices.data_created), benefit_name, ' \
                            'benefit_description, url || url_suffix AS url_address \
                      FROM flats \
                      JOIN projects ON flats.project_id = projects.project_id \
                      JOIN prices ON flats.flat_id = prices.price_id ' \
                  f'WHERE city LIKE "{flats_filter["city"]}" ' \
                  f'AND name LIKE "{flats_filter["name"]}" ' \
                  f'AND rooms = {flats_filter["rooms"]} ' \
                  f'AND price <= {flats_filter["max_price"]} ' \
                  f'AND settlement_date <= "{flats_filter["max_settlement_date"]}" ' \
                  f'AND finishing = {flats_filter["finishing"]} ' \
                  'GROUP BY flat_id ORDER BY price) ' \
                  f'WHERE booking_status LIKE "{flats_filter["booking_status"]}"'
    return execute_sql_fetch(sql_request)


def get_one_field_info(table: str, field: str) -> list[tuple | None]:
    """
    Возвращает информацию по одному полю из базы данных,
    одинаковые записи группируются (удаляются).
    Например для получения информации о доступных ЖК
    или городов по которым есть информация в базе данных.

    :param table: Название таблицы в базе данных.
    :param field: Название поля в указанной таблице.
    :return: Список кортежей или пустой список.
    """
    return execute_sql_fetch(f"""SELECT {field} FROM {table} GROUP BY {field}""")


def remove_duplicates_in_prices_table() -> None:
    """
    Удаляет одинаковые цены из таблицы prices
    (если цена не изменилась, равна предыдущей
    цене и не изменился статус бронирования, то
    такая запись будет удалена).
    """
    execute_sql("""DELETE FROM prices WHERE rowid NOT IN 
                (SELECT min(rowid) FROM prices GROUP BY price_id, price, booking_status)""")


if __name__ == '__main__':
    create_db()
    # drop('projects', 'flats', 'prices')
