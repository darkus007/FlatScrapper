"""
Основной модуль сбора информации по квартирам,
результат сохраняет в базу данных.
"""
from pik import pik_scrapper
from database import database


def scrapping():
    projects, flats, prices = pik_scrapper.run()
    database.create()
    database.save_to_database('projects', projects)
    database.save_to_database('flats', flats)
    database.save_to_database('prices', prices)
    database.remove_duplicates_prices_table()


if __name__ == '__main__':
    scrapping()
