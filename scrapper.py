"""
Основной модуль сбора информации по квартирам,
результат сохраняет в базу данных.
"""

from pik import pik_scrapper
from database import database


def scrapping():
    projects, flats, prices = pik_scrapper.run()
    database.save_to_database('projects', projects)
    database.save_to_database('flats', flats)
    database.save_to_database('prices', prices)
    database.remove_duplicates_in_prices_table()


if __name__ == '__main__':
    scrapping()
    # res = database.get_flat(422)
    # print(res)
    # res = database.get_flats_by_filter(database.flats_filter)
    # res = database.get_flats_by_filter_last_price(database.flats_filter)
    # services.save_to_excel_file(res, 'temp/file')
    # for r in res:
    #     print(r)
