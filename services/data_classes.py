"""
Модуль содержит дата-классы представления собранных данных,
класс для преобразования дата-классов в json объект.
"""

from dataclasses import dataclass, is_dataclass, asdict
from json import JSONEncoder


@dataclass
class Flat:                     # Информация о квартире
    flat_id: int                # id квартиры
    address: str                # Адрес
    floor: int                  # Этаж
    rooms: int                  # Количество комнат
    area: float                 # Площадь квартиры
    finishing: bool             # Отделка
    bulk: str                   # Корпус дома
    settlement_date: str        # Дата заселения
    url_suffix: str             # Приставка к url адресу квартиры, полный адрес будет Project.url + Flat.url_suffix
    benefit_name: str           # Название ценового предложения
    benefit_description: str    # Описание ценового предложения
    price: int                  # Цена
    meter_price: int            # Цена за метр
    booking_status: str         # Статус бронирования


@dataclass
class Project:              # Информация о ЖК
    id: int                 # id ЖК
    name: str               # Название ЖК
    url: str                # URL адрес ЖК
    metro: str              # Название метро
    time_to_metro: int      # Расстояние до метро
    longitude: float        # Координаты ЖК
    latitude: float         # Координаты ЖК
    total_flats: int        # Всего квартир в ЖК
    flats: list[Flat]       # Информация об этих квартирах


class JsonDataclassEncoder(JSONEncoder):
    """
    Используется для преобразования дата-классов в json объект.
    Пример json.dumps(dataclass, ensure_ascii=False, cls=JsonDataclassEncoder).
    """
    def default(self, obj):
        if is_dataclass(obj):
            return asdict(obj)
        return super().default(obj)
