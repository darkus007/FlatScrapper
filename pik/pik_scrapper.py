"""
Модуль сбора информации с сайта застройщика pik.


Информацию о проектах (Жилых Комплексах) получаем на главной странице "https://www.pik.ru/projects".
Важно получить id ЖК.

Запрос к api сайта для получения информации о квартирах в одном конкретном ЖК выглядит так
https://api.pik.ru/v2/filter?customSort=1&type=1,2&location=2,3&block=1124&flatPage=1&flatLimit=50&onlyFlats=1
где:
    &location=2,3 - локация, в данном случае 2,3 это Москва и Область;
    &block=1124 - код жилого комплекса (его id), получаем на главной странице "https://www.pik.ru/projects";
    &flatPage=1 - api отдает информацию постранично
    &flatLimit=50 - в количестве 50 квартир на страницу.
"""

__version__ = "v. 1.0 dated 29/11/2022"

import re
import requests
from bs4 import BeautifulSoup
from time import sleep
from random import randint

from settings import *
from services import *

HOST = "https://www.pik.ru/projects"
PROJECT_URL_PREFIX = "https://www.pik.ru/"


def get_html(url: str, params: str = None) -> requests.Response | str:
    """
    Возвращает html страницу или пустую строку.
    :param url: URL-адрес.
    :param params: Дополнительные параметры.
    :return: :class:`Response <Response>` object
    :rtype: requests.Response
    """
    for i in range(3):  # три попытки получить страницу
        try:
            rq = requests.get(url, params=params, headers=HEADERS)
            if rq.status_code == 200:
                print(f"{rq.status_code}: {url}")
                return rq
            else:
                print(f"ERROR {rq.status_code}: {url}.")
        except Exception as ex:
            print(f"Ошибка получения страницы {ex}.")
    return ''


def get_projects(html: str) -> set[tuple[str, str]]:
    """
    Возвращает id и название проектов.

    :param html: HTML страница с проектами.
    :return: Множество кортежей с id и именем найденных проектов.
             ID будет использован для формирования URL запроса
             на получение информации о квартирах.
    """
    soup = BeautifulSoup(html, 'lxml')
    all_projects = soup.find("script", id="__NEXT_DATA__").text

    # "value":149,"text":"Одинцово-1","active":false
    match = re.findall(r'"value":([\d]+),"text":"([\w -]+)","active":', all_projects)  # [("id", "name"), ...]
    print(f"Найдено {len(set(match))} ЖК.")

    return set(match)  # удаляем дубликаты и возвращаем


def _get_flats_from_one_project(project: tuple) -> dict:
    """
    Возвращает все найденные квартиры в рамках одного ЖК.

    :param project: Кортеж с id и названием ЖК ("id", "name").
    :return: Словарь с информацией о ЖК и квартирах в нем.
    """
    flat_page = 1
    url = "https://api.pik.ru/v2/filter?customSort=1&type=1,2&location=2,3&block=" \
          + f"{project[0]}&flatLimit=50&onlyFlats=1&flatPage="

    flats_info = get_html(url=url + str(flat_page)).json()

    if DEBUG:
        write_json_to_file(f'../temp/raw_flats_info_{get_data_time()}', flats_info)
    # flats_info = read_json_from_file('flats_info.json')

    total_flats = flats_info.get('count', 0)
    total_pages = total_flats // 50
    if total_flats % 50 != 0:
        total_pages += 1
    print(f"ЖК '{project[1]}' всего квартир {total_flats}.")
    print(f"На {total_pages} страницах.")

    # получаем информацию о ЖК
    result = {
        "id": get_value_from_json(flats_info, ['blocks', 0, "id"]),
        "name": get_value_from_json(flats_info, ['blocks', 0, "name"]),
        "url": PROJECT_URL_PREFIX + get_value_from_json(flats_info, ['blocks', 0, "url"]),
        "metro": get_value_from_json(flats_info, ['blocks', 0, "metro"]),
        "time_to_metro": get_value_from_json(flats_info, ['blocks', 0, "timeOnFoot"]),
        "longitude": get_value_from_json(flats_info, ['blocks', 0, "longitude"]),
        "latitude": get_value_from_json(flats_info, ['blocks', 0, "latitude"]),
        "total_flats": get_value_from_json(flats_info, ['count']),
        "flats": []
    }

    # собираем информацию о квартирах в этом ЖК
    flats_on_this_page = get_value_from_json(flats_info, ['blocks', 0, "flats"])  # list[dict]
    result["flats"] = _get_flats_from_page(flats_on_this_page)

    for flat_page in range(2, total_pages + 1):
        print(f"{flat_page=}")
        flats_info = get_html(url=url + str(flat_page)).json()
        if DEBUG:
            write_json_to_file(f'../temp/raw_flats_info_{get_data_time()}', flats_info)
        flats_on_this_page = get_value_from_json(flats_info, ['blocks', 0, "flats"])  # list[dict]
        result["flats"] += _get_flats_from_page(flats_on_this_page)

        sleep(randint(1, 3))

    print(f"Собрана информация по {len(result['flats'])} квартирам.")

    return result


def _get_flats_from_page(flats_on_page: json) -> list[dict]:
    """
    Собирает информацию о квартирах на странице.

    :param flats_on_page: json с данными о квартирах.
    :return: Список словарей с данными о найденных квартирах.
             Один словарь на одну квартиру.
    """
    result = []
    for flat in flats_on_page:
        result_flats = {
            "flat_id": get_value_from_json(flat, ["id"]),
            "address": get_value_from_json(flat, ["address"]),
            "floor": get_value_from_json(flat, ["floor"]),
            "rooms": get_value_from_json(flat, ["rooms"]),
            "area": get_value_from_json(flat, ["area"]),
            "finishing": get_value_from_json(flat, ["finish"]),
            "bulk": get_value_from_json(flat, ["bulk", "name"]),
            "settlementDate": get_value_from_json(flat, ["bulk", "settlementDate"]),
            "url_suffix": "/flats/" + str(get_value_from_json(flat, ["id"])),

            "benefit_name": get_value_from_json(flat, ['mainBenefit', "name"]),
            "benefit_description": get_value_from_json(flat, ['mainBenefit', "description"]),
            "price": get_value_from_json(flat, ["price"]),
            "meter_price": get_value_from_json(flat, ["meterPrice"]),
            "booking_status": get_value_from_json(flat, ["bookingStatus"]),
        }

        result.append(result_flats)
    return result


def get_flats_from_all_projects(all_projects: set[tuple[str, str]]) -> list[dict]:
    """
    Собирает информацию о квартирах во всех найденных ЖК.

    :param all_projects: Множество (set) кортежей с id и названием ЖК {("id", "name"), ...}.
    :return: Список с информацией о ЖК и квартирах в виде словаря.
    """
    res = []
    for project in all_projects:
        res.append(_get_flats_from_one_project(project))
        break
    return res


if __name__ == '__main__':
    html_text = get_html(HOST).text

    if DEBUG:
        with open('../temp/main_page.html', 'w') as file:
            file.write(html_text)

    # html_text = read_from_file('index.html')
    projects = get_projects(html_text)
    all_info = get_flats_from_all_projects(projects)
    write_json_to_file("../temp/all_flat_info", all_info)
