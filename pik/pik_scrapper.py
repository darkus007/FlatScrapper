"""
Модуль сбора информации с сайта застройщика PIK.

Информацию о проектах (Жилых Комплексах) получаем на главной странице "https://www.pik.ru/projects".
Важно получить id ЖК. Квартиры получаем через api.

Запрос к api сайта для получения информации о квартирах в одном конкретном ЖК выглядит так
https://api.pik.ru/v2/filter?customSort=1&type=1,2&location=2,3&block=1124&flatPage=1&flatLimit=50&onlyFlats=1
где:
    &location=2,3 - локация, в данном случае 2,3 это Москва и Область;
    &block=1124 - код жилого комплекса (его id), получаем на главной странице "https://www.pik.ru/projects";
    &flatPage=1 - api отдает информацию постранично
    &flatLimit=50 - в количестве 50 квартир на страницу.
"""

__version__ = "v. 1.0 dated 01/11/2022"

import re
import requests
from bs4 import BeautifulSoup
from time import sleep
from random import randint
from sys import getsizeof

import settings
from settings import *
from services import *

HOST = "https://www.pik.ru/projects"  # страница с проектами
PROJECT_URL_PREFIX = "https://www.pik.ru/"  # для формирования url-адреса проекта

logger = init_logger(__name__, settings.LOGGER_LEVEL)
logging.getLogger('urllib3').setLevel(logging.ERROR)


def _get_html(url: str, params: str = None) -> requests.Response | str:
    """
    Возвращает класс requests.Response или пустую строку.

    :param url: URL-адрес.
    :param params: Дополнительные параметры.
    :return: :class:`Response <Response>` object или пустую строку.
    """
    for i in range(3):  # три попытки получить страницу
        try:
            rq = requests.get(url, params=params, headers=HEADERS)
            if rq.status_code == 200:
                logger.debug(f"{rq.status_code}: {url}")
                return rq
            else:
                logger.error(f"{rq.status_code}: {url}")
                sleep(3)
        except Exception as ex:
            logger.error(f"Функция _get_html вызвала исключение {ex}")
    return ''


def _get_projects(html: str) -> set[tuple[str, str]]:
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
    res = set(match)  # удаляем дубликаты (квартиры часто повторяются, видимо для усложнения парсинга)
    logger.debug(f"Найдено {len(res)} ЖК.")

    return res


def _get_flats_from_one_project(data: str, project: tuple) -> tuple[list[Project], list[Flat], list[Price]]:
    """
    Возвращает все найденные квартиры одного ЖК.

    :param data: Текущая дата в формате '%Y-%m-%d'.
    :param project: Кортеж с id и названием ЖК ("id", "name").
    :return: Кортеж списков с информацией о ЖК, квартирах в нем и их цене.
    """
    flat_page = 1
    url = "https://api.pik.ru/v2/filter?customSort=1&type=1,2&location=2,3&block=" \
          + f"{project[0]}&flatLimit=50&onlyFlats=1&flatPage="

    flats_info = _get_html(url=url + str(flat_page)).json()

    if DEBUG:
        write_json_to_file(f'temp/raw_flats_info_{get_data_time()}', flats_info)
    # flats_info = read_json_from_file('flats_info.json')

    total_flats = flats_info.get('count', 0)
    total_pages = total_flats // 50
    if total_flats % 50 != 0:
        total_pages += 1

    logger.debug(f"ЖК '{project[1]}' всего квартир {total_flats}.")
    logger.debug(f"На {total_pages} страницах.")

    full_address = get_value_from_json(flats_info, ['blocks', 0, "flats", 0, "address"])
    project_city = full_address.split(',')[0]
    project_address = re.sub(r'[, (]*[Кк]орп[уса]*[\d\w ,./()№]*', '', full_address)       # убираем корпуса
    project_address = re.sub(r'[, ]*[Ээ]тап[ы]*[\d .,/]+', '', project_address)            # убираем этапы

    # получаем информацию о ЖК
    result_project = [Project(
        project_id=get_value_from_json(flats_info, ['blocks', 0, 'id']),
        city=project_city,
        name=get_value_from_json(flats_info, ['blocks', 0, 'name']),
        url=PROJECT_URL_PREFIX + get_value_from_json(flats_info, ['blocks', 0, 'url']),
        metro=get_value_from_json(flats_info, ['blocks', 0, 'metro']),
        time_to_metro=get_value_from_json(flats_info, ['blocks', 0, 'timeOnFoot']),
        longitude=get_value_from_json(flats_info, ['blocks', 0, 'longitude']),
        latitude=get_value_from_json(flats_info, ['blocks', 0, 'latitude']),
        address=project_address,
        data_created=data
    )]

    # собираем информацию о квартирах в этом ЖК
    flats_on_this_page = get_value_from_json(flats_info, ['blocks', 0, "flats"])  # list[dict]
    result_flats, result_prices = _get_flats_from_page(data, result_project[0].project_id, flats_on_this_page)

    for flat_page in range(2, total_pages + 1):
        logger.debug(f"[{flat_page=}/{total_pages}]")
        flats_info = _get_html(url=url + str(flat_page)).json()
        if DEBUG:
            write_json_to_file(f'temp/raw_flats_info_{get_data_time()}', flats_info)
        flats_on_this_page = get_value_from_json(flats_info, ['blocks', 0, "flats"])  # list[dict]
        temp_flats, temp_prices = _get_flats_from_page(data, result_project[0].project_id, flats_on_this_page)
        result_flats.extend(temp_flats)
        result_prices.extend(temp_prices)

        sleep(randint(1, 3))

    logger.debug(f"Собрана информация по {len(result_flats)} квартирам.")

    return result_project, result_flats, result_prices


def _get_flats_from_page(data: str, project_id: int, flats_on_page: json) -> tuple[list[Flat], list[Price]]:
    """
    Собирает информацию о квартирах и их цене на странице.

    :param data: Текущая дата в формате '%Y-%m-%d'.
    :param project_id: id ЖК для указания принадлежности найденных квартир к этому ЖК.
    :param flats_on_page: json с данными о квартирах.
    :return: Кортеж списков с данными о найденных квартирах и ценах.
    """
    result_flats = []
    result_prices = []
    for flat in flats_on_page:
        result_flat = Flat(
            flat_id=get_value_from_json(flat, ["id"]),
            project_id=project_id,
            address=get_value_from_json(flat, ["address"]),
            floor=get_value_from_json(flat, ["floor"]),
            rooms=get_value_from_json(flat, ["rooms"]),
            area=get_value_from_json(flat, ["area"]),
            finishing=get_value_from_json(flat, ["finish"]),
            bulk=get_value_from_json(flat, ["bulk", "name"]),
            settlement_date=get_value_from_json(flat, ["bulk", "settlementDate"]),
            url_suffix="/flats/" + str(get_value_from_json(flat, ["id"])),
            data_created=data
        )
        result_price = Price(
            price_id=result_flat.flat_id,
            benefit_name=get_value_from_json(flat, ['mainBenefit', "name"]),
            benefit_description=get_value_from_json(flat, ['mainBenefit', "description"]),
            price=get_value_from_json(flat, ["price"]),
            meter_price=get_value_from_json(flat, ["meterPrice"]),
            booking_status=get_value_from_json(flat, ["bookingStatus"]),
            data_created=data
        )
        result_flats.append(result_flat)
        result_prices.append(result_price)
    return result_flats, result_prices


def _get_flats_from_all_projects(data: str, all_projects: set[tuple[str, str]]) -> tuple[list[Project],
                                                                                         list[Flat], list[Price]]:
    """
    Собирает информацию о квартирах во всех найденных ЖК.

    :param data: Текущая дата в формате '%Y-%m-%d'.
    :param all_projects: Множество (set) кортежей с id и названием ЖК {("id", "name"), ...}.
    :return: Кортеж списков с информацией о всех ЖК, квартирах в ЖК и цене квартир.
    """
    result_projects = []
    result_flats = []
    result_prices = []
    current_project_number = 1
    total_projects = len(all_projects)

    for project in all_projects:
        logger.debug(f"[{current_project_number}|{total_projects}] ЖК.")
        project, flats, prices = _get_flats_from_one_project(data, project)
        result_projects.extend(project)
        result_flats.extend(flats)
        result_prices.extend(prices)
        current_project_number += 1
        # break

    logger.info(f"Собрана информация по {len(result_projects)} ЖК, в которых найдено {len(result_flats)} квартир.")
    logger.debug(f'Всего {getsizeof(result_projects) + getsizeof(result_flats) + getsizeof(result_prices)} bytes.')

    return result_projects, result_flats, result_prices


def run() -> tuple[list[Project], list[Flat], list[Price]]:
    """
    Запускает сбор информации о квартирах от застройщика PIK.

    :return: Кортеж списков с информацией о всех ЖК, квартирах в ЖК и цене квартир.
    """
    current_data = get_data_time('%Y-%m-%d')

    logger.info(f"Начало сбора информации.")

    html_text = _get_html(HOST)  # AttributeError: 'str' object has no attribute 'text'
    if html_text != '':
        html_text = html_text.text

        if DEBUG:
            with open('temp/main_page.html', 'w') as file:
                file.write(html_text)
        # html_text = read_from_file('index.html')

        projects = _get_projects(html_text)
        return _get_flats_from_all_projects(current_data, projects)
    else:
        logger.error(f"Не удалось получить главную страницу {HOST}!")


if __name__ == '__main__':
    projects, flats, prices = run()
    write_json_to_file("../temp/all_projects", projects)
    write_json_to_file("../temp/all_flats", flats)
    write_json_to_file("../temp/all_prices", prices)
    # json_data = json.loads(json.dumps(all_info, ensure_ascii=False, cls=JsonDataclassEncoder))
