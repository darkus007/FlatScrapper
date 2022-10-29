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

import settings
from services import *


HOST = "https://www.pik.ru/projects"
PROJECT_URL_PREFIX = "https://www.pik.ru/"


def get_html(url, params=None) -> requests.Response | str:
    """
    Возвращает html страницу или пустую строку.
    :param url: URL-адрес.
    :param params: Дополнительные параметры.
    :return: :class:`Response <Response>` object
    :rtype: requests.Response
    """
    try:
        rq = requests.get(url, params=params, headers=settings.HEADERS)
        if settings.DEBUG:
            write_to_file("index.html", rq.text)
        return rq
    except Exception as ex:
        print(ex)
        return ''


def get_projects(html: str) -> set[tuple[str, str]]:
    """
    Возвращает id и название проектов.

    :param html: HTML страница с проектами.
    :return: Множество кортежей с id и именем найденных проектов.
             ID будет использован для формирования URL запроса на получение квартир.
    """
    soup = BeautifulSoup(html, 'lxml')
    all_projects = soup.find("script", id="__NEXT_DATA__").text

    # "value":149,"text":"Одинцово-1","active":false
    match = re.findall(r'"value":([\d]+),"text":"([\w -]+)","active":', all_projects)  # [("id", "name"), ...]

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
    # write_json_to_file('flats_info', flats_info.json())
    # flats_info = read_json_from_file('flats_info.json')

    total_flats = flats_info['count']
    total_pages = total_flats // 50 + 1
    print(f"{total_flats=}")
    print(f"{total_pages=}")

    # получаем информацию о ЖК
    result = {
        "project_name": flats_info['blocks'][0]["name"],
        "url": PROJECT_URL_PREFIX + flats_info['blocks'][0]["url"],
        "metro": flats_info['blocks'][0]["metro"],
        "time_to_metro": flats_info['blocks'][0]["timeOnFoot"],
        "longitude": flats_info['blocks'][0]["longitude"],
        "latitude": flats_info['blocks'][0]["latitude"],
        "total_flats": flats_info['count'],
        "flats": []
    }

    # собираем информацию о квартирах в этом ЖК
    flats_on_this_page = flats_info['blocks'][0]["flats"]    # list[dict]
    result["flats"] = _get_flats_from_page(flats_on_this_page)

    for flat_page in range(2, total_pages + 1):
        print(f"{flat_page=}")
        print(f"URL: {url + str(flat_page)}")
        flats_info = get_html(url=url + str(flat_page)).json()
        flats_on_this_page = flats_info['blocks'][0]["flats"]  # list[dict]
        result["flats"] += _get_flats_from_page(flats_on_this_page)

        sleep(randint(1, 3))

    print(f"Total flats {len(result['flats'])}")

    return result


def _get_flats_from_page(flats_on_page: json) -> list[dict]:
    """
    Собирает информацию о квартирах на странице.

    :param flats_on_page: json с данными о квартирах.
    :return: Список словарей с данными о найденных квартирах.
    """
    result = []
    for flat in flats_on_page:
        result_flats = {
            "address": flat['address'],
            "floor": flat['floor'],
            "rooms": flat['rooms'],
            "price": flat['price'],
            "area": flat['area'],
            "booking_status": flat['bookingStatus'],
            "benefit_name": flat['mainBenefit']["name"],
            "benefit_description": flat['mainBenefit']["description"],
            "bulk": flat['bulk']["name"],
            "settlementDate": flat['bulk']["settlementDate"],
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
    return res


if __name__ == '__main__':
    html_text = get_html(HOST).text
    # html_text = read_from_file('index.html')
    projects = get_projects(html_text)
    all_info = get_flats_from_all_projects(projects)
    print(all_info)
    write_json_to_file("all_flat_info", all_info)
